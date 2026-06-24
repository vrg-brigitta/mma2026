import json
import re
import threading
from collections import Counter
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from src import config


class QueryHandler:
    """
    Open source LLM handler for the search and describe functionalities
        llm_handler.preprocess(user_query)
        llm_handler.describe(metadata_records)

    Downloads the model from Hugging Face if not already downloaded.
    """

    MODEL_NAME = "mistralai/Ministral-8B-Instruct-2410"
    METADATA_FIELDS = ('culture', 'period', 'type', 'genre',
                       'description', 'clip_description')

    def __init__(self, model_name=None):
        self.model_name = model_name or QueryHandler.MODEL_NAME
        self.lock = threading.Lock()
        self.tokenizer = None
        self.model = None

    def load_model(self):
        """Download/load the tokenizer and model"""
        if self.model is not None:
            return

        print('Loading LLM', self.model_name, 'on', config.DEVICE)
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            dtype=torch.float16 if config.DEVICE == 'cuda' else torch.float32,
        ).to(config.DEVICE)

    def _generate(self, system_prompt, user_prompt, max_new_tokens=512):
        """Run a single chat completion and return the decoded output string."""
        self.load_model()

        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt},
        ]
        inputs = self.tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            return_tensors='pt',
        ).to(config.DEVICE)

        with torch.no_grad():
            output = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                pad_token_id=self.tokenizer.eos_token_id,
            )

        generated = output[0][inputs["input_ids"].shape[-1]:]
        return self.tokenizer.decode(generated, skip_special_tokens=True)

    @staticmethod
    def _parse_json(text):
        """Extract the first JSON object from the model output."""
        try:
            return json.loads(text)
        except (ValueError, TypeError):
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except ValueError:
                    pass
        print('Could not parse JSON from LLM output:', text)
        return None

    @staticmethod
    def _summarize_metadata(metadata_records):
        """
        Summarizes the metadata for the "describe" task to not feed the LLM repetitive information.
        """
        summary = {}
        for field in QueryHandler.METADATA_FIELDS:
            counts = Counter(
                str(record[field]).strip()
                for record in metadata_records
                if record.get(field) not in (None, '')
            )
            if counts:
                summary[field] = dict(counts)
        return summary

    def _search_system_prompt(self):
        return (
            """<task>
            Convert the user's art-image search question into a structured query for retrieval and boolean filtering over metadata.

            <fields>
            culture: origin/people (e.g. Japanese, Egyptian)
            period: era/dynasty (e.g. Edo period, Renaissance)
            type: object type (e.g. painting, woodblock print)
            genre: subject/theme (e.g. landscape, portrait)
            </fields>

            <rules>
            - Use ONLY information stated in the query. Never add cultures, periods, types, genres, or details the user did not mention.
            - Fill a field only if the query implies it, else use [].
            - Synonyms allowed only as close wording variants of terms already in the query.
            - search_query: one plain sentence restating the wanted image. No boolean operators.
            - boolean_query: OR-group synonyms, AND-join distinct concepts, every term in double quotes. Use "" if no constraints.
            - Output ONLY the JSON object. No other text.
            </rules>

            <output>
            {"terms": {"culture": [], "period": [], "type": [], "genre": []}, "search_query": "", "boolean_query": ""}
            </output>

            <example>
            user: old Japanese woodblock prints of waves
            output: {"terms": {"culture": ["Japanese"], "period": [], "type": ["woodblock print"], "genre": []}, "search_query": "An old Japanese woodblock print of waves", "boolean_query": "\\"Japanese\\" AND \\"woodblock print\\" AND \\"waves\\""}
            </example>
            </task>"""
        )

    def query_to_dict(self, user_query):
        """
        Rephrase the user query into a keyword/embedding search.
        Returns a dict (or None if parsing failed).
        """
        with self.lock:
            raw = self._generate(self._search_system_prompt(), user_query)
        return QueryHandler._parse_json(raw)

    def dict_to_clip_query(self, query_dict):
        """Convert the structured query dict from the LLM into a text query for CLIP.

        Example:
            Input:
                {
                    "terms": {"culture": ["Japanese"], "period": [], "type": ["woodblock print"], "genre": []},
                    "search_query": "An old Japanese woodblock print of waves",
                    "boolean_query": "\"Japanese\" AND \"woodblock print\" AND \"waves\""
                }
            Output:
                An old Japanese woodblock print of waves
                Culture: Japanese
                period: any
                type: woodblock print
                genre: any

                Required terms:
                Japanese
                woodblock print
                waves
        """
        search_query = query_dict.get("search_query", "")
        terms = query_dict.get("terms", {})
        boolean_query = query_dict.get("boolean_query", "")

        lines = [search_query]
        for field in ["culture", "period", "type", "genre"]:
            values = terms.get(field, [])
            line = f"{field.capitalize()}: {', '.join(values) if values else 'any'}"
            lines.append(line)

        lines.append("\nRequired terms:")
        for term in boolean_query.split("AND"):
            term = term.strip().strip('"')
            if term:
                lines.append(term)

        return "\n".join(lines)

    def to_clip_query(self, user_query):
        """Convenience method to convert a raw user query into a CLIP search query."""
        structured = self.query_to_dict(user_query)
        if structured is None:
            return None
        return self.dict_to_clip_query(structured)

    def _describe_system_prompt(self):
        return (
            """<task>
            Describe one cluster of artworks. Start with a general description of the artworks then summarize the key insights for each of the following: culture, period, type, genre; one bullet point each. Then suggest follow-up search queries to help the user explore the cluster further.
            <fields>
            culture: origin/people (e.g. Japanese, Egyptian)
            period: era/dynasty (e.g. Edo period, Renaissance)
            type: object type (e.g. painting, woodblock print)
            genre: subject/theme (e.g. landscape, portrait)
            description: standard textual description
            </fields>
            <rules>
            - Each value has a count = how many artworks have it. Higher count = more dominant, for example: "culture: Chinese, 100" means 100 artworks are Chinese.
            - A field can have 1, 2, or more distinct values. Rank ALL given values by count, not just the top two — if three or more cultures are present, mention how they rank against each other, not just the top one vs. the rest.
            - If a field has only one distinct value, state that the cluster is uniform on that field (100% one value) rather than describing it as "dominant" over something else, since there's nothing to compare it to.
            - Use ONLY the given data. Never invent cultures, periods, types, genres, or details.
            - When citing counts, place the number directly next to the value it belongs to (e.g. "Japanese culture (120) outweighs Chinese (30)"), not as a separate comparison clause.
            - Write trends as natural, flowing sentences, not just data restatements.
            - summary: A short paragraph describing the artworks.
            - trends: 4 bullet-style strings containing key insights for the culture, period, type and genre (i.e. the number of occurrences, which is dominant, and any links to the descriptions).
            - suggestions: A list of exactly 2 natural language search queries, ordered from most to least interesting, that a user could submit to explore this cluster more deeply. Each suggestion should be grounded in the dominant metadata values found in the cluster and informed by patterns or contrasts observed in the summary and trends. Frame them as something a curious user might naturally ask next, not as restatements of the cluster. Vary the angle across suggestions — for example, drilling into a subtype, contrasting a minority culture, exploring a thematic thread from the descriptions, or shifting to an adjacent period. Make sure that the questions start with either "Show me" or "Find me". Never say "compare" or "contrast" in the suggestions, since the user will be exploring one cluster at a time.
            - Output ONLY the JSON object. No other text.
            </rules>
            <output>
            {"summary": "", "trends": [], "suggestions": []}
            </output>
            <example>
            user: culture: German, 40; culture: French, 25; culture: Dutch, 15; culture: Russian, 5; period: 18th century, 85; type: Porcelain, 60; type: Glass, 25; genre: European Sculpture and Decorative Arts, 85; description: "A ladle, typically used for serving soups or stews"; description: "A figure in the form of a nodding pagoda"; description: "A jug"; description: "A goblet"; description: "A group of monkeys"
            output: {"summary": "An 18th-century cluster of European decorative arts, led by German pieces but with a meaningful spread across French, Dutch, and Russian origins, made up mostly of porcelain alongside a smaller share of glass objects such as jugs and goblets.", "trends": ["German culture (40) leads the cluster, followed by French (25), Dutch (15), and a small Russian presence (5)", "Every piece in the cluster is dated to the 18th century (85), making it fully uniform on period", "Porcelain (60) is the more common object type, ahead of Glass (25), reflected in descriptions of ladles, figures, and pagodas alongside jugs and goblets", "European Sculpture and Decorative Arts (85) is the only genre present, so the cluster is uniform here too"], "suggestions": ["Show me French and Dutch decorative glass objects from the 18th century", "Find decorative arts featuring animal motifs like monkeys"]}
            </example>
            </task>"""
        )

    def describe(self, metadata_records):
        """
        Describe patterns in the selected cluster.
        Returns a dict (or None if parsing failed).
        """
        metadata_summary = QueryHandler._summarize_metadata(metadata_records)
        user_prompt = json.dumps({'metadata_summary': metadata_summary}, indent=2)

        with self.lock:
            print('Describe requested for', len(metadata_records), 'artworks')
            raw = self._generate(self._describe_system_prompt(), user_prompt)
        return QueryHandler._parse_json(raw)


query_handler = QueryHandler()
query_handler.load_model()
