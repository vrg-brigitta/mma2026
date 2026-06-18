import json
import torch
import torch.nn.functional as F
import clip
from src import config
import numpy as np


class CLIPHandler:
    """
    CLIP handler for text-to-image search over precomputed embeddings.

    Usage:
        clip_handler = CLIPHandler()
        clip_handler.load_model()
        clip_handler.load_embeddings()
        ids, scores = clip_handler.search_by_text(user_query)
    """

    _model_cache = {}

    def __init__(self):
        self.model_name = config.CLIP_MODEL
        self.embeddings_path = config.EMBEDDINGS_PATH
        self.ids_path = config.IDS_PATH

        self.model = None
        self.ids = None
        self.embeddings = None

    def load_model(self):
        print('Loading CLIP model', self.model_name, 'on', config.DEVICE)
        key = (self.model_name, config.DEVICE)

        if key not in CLIPHandler._model_cache:
            model, _ = clip.load(self.model_name, device=config.DEVICE)
            model.eval()
            CLIPHandler._model_cache[key] = model

        self.model = CLIPHandler._model_cache[key]
        return self.model

    def load_embeddings(self, embeddings_path=None, ids_path=None):
        print('Loading CLIP embeddings from', self.embeddings_path)
        embeddings_path = embeddings_path or self.embeddings_path
        ids_path = ids_path or self.ids_path

        if embeddings_path is None or ids_path is None:
            raise ValueError("embeddings_path and ids_path must be provided")

        self.embeddings = np.load(embeddings_path)

        with open(ids_path, "r") as f:
            self.ids = json.load(f)

        return self.ids, self.embeddings

    def encode_text(self, query: str):
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        with torch.no_grad():
            tokens = clip.tokenize([query], truncate=True).to(config.DEVICE)
            text_features = self.model.encode_text(tokens)
            text_features = F.normalize(text_features, dim=-1)

        return text_features.cpu().numpy()[0]

    def search_by_text(self, query, threshold=0.25):
        if self.embeddings is None or self.ids is None:
            raise RuntimeError("Embeddings not loaded. Call load_embeddings() first.")

        q = self.encode_text(query)

        scores = self.embeddings @ q
        idxs = np.where(scores >= threshold)[0]

        order = idxs[np.argsort(-scores[idxs])]

        ranked_ids = [self.ids[i] for i in order]
        ranked_scores = [float(scores[i]) for i in order]

        return ranked_ids, ranked_scores


clip_handler = CLIPHandler()
clip_handler.load_model()