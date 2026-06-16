import json
import re
import threading
from collections import Counter

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


class LLMHandler:
    """
    Open source LLM handler for the search and describe functionalities
        llm_handler.search(user_query)
        llm_handler.describe(metadata_records)

    Downloads the model from Hugging Face if not already downloaded.
    """

    MODEL_NAME = "mistralai/Ministral-8B-Instruct-2410"
    METADATA_FIELDS = ('culture', 'period', 'type', 'genre', 'description', 'clip_description')

    def __init__(self, model_name=None):
        self.model_name = model_name or LLMHandler.MODEL_NAME
        self.device = 'cuda' if torch.cuda.is_available() else ('mps' if torch.backends.mps.is_available() else 'cpu')
        self.lock = threading.Lock()
        self.tokenizer = None
        self.model = None

    def load_model(self):
        """Download/load the tokenizer and model"""
        if self.model is not None:
            return

        print('Loading LLM', self.model_name, 'on', self.device)
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.float16 if self.device == 'cuda' else torch.float32,
        ).to(self.device)
        print('LLM loaded')

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
        ).to(self.device)

        with torch.no_grad():
            output = self.model.generate(
                inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                pad_token_id=self.tokenizer.eos_token_id,
            )

        generated = output[0][inputs.shape[-1]:]
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
        for field in LLMHandler.METADATA_FIELDS:
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

    def search(self, user_query):
        """
        Rephrase the user query into a keyword/embedding search.
        Returns a dict (or None if parsing failed).
        """
        with self.lock:
            print('Search requested for query:', user_query)
            raw = self._generate(self._search_system_prompt(), user_query)
        return LLMHandler._parse_json(raw)


    def _describe_system_prompt(self):
        return (
           """<task>
            Describe one cluster of artworks. Identify which cultures, periods, types, and genres dominate, and note anything notable.

            <fields>
            culture: origin/people (e.g. Japanese, Egyptian)
            period: era/dynasty (e.g. Edo period, Renaissance)
            type: object type (e.g. painting, woodblock print)
            genre: subject/theme (e.g. landscape, portrait)
            description: standard textual description
            clip_description: CLIP-generated visual description
            </fields>

            <rules>
            - Each value has a count = how many artworks have it. Higher count = more dominant.
            - Example: "culture: Chinese, 100" means 100 artworks are Chinese.
            - Rank values by count to find what dominates each field.
            - Use ONLY the given data. Never invent cultures, periods, types, genres, or details.
            - summary: one plain sentence describing the cluster overall.
            - trends: short bullet-style strings, most dominant first. Be specific, mention counts where useful.
            - Output ONLY the JSON object. No other text.
            </rules>

            <output>
            {"summary": "", "trends": []}
            </output>

            <example>
            user: culture: Japanese, 120; culture: Chinese, 30; period: Edo period, 110; type: woodblock print, 130; genre: landscape, 90; genre: portrait, 25
            output: {"summary": "A predominantly Japanese cluster of Edo-period woodblock prints, mostly landscapes.", "trends": ["Japanese culture dominates (120 vs 30 Chinese)", "Mostly Edo period (110)", "Almost all woodblock prints (130)", "Landscapes outnumber portraits (90 vs 25)"]}
            </example>
            </task>"""
        )

    def describe(self, metadata_records):
        """
        Describe patterns in the selected cluster.
        Returns a dict (or None if parsing failed).
        """
        metadata_summary = LLMHandler._summarize_metadata(metadata_records)
        user_prompt = json.dumps({'metadata_summary': metadata_summary}, indent=2)

        with self.lock:
            print('Describe requested for', len(metadata_records), 'artworks')
            raw = self._generate(self._describe_system_prompt(), user_prompt)
        return LLMHandler._parse_json(raw)
