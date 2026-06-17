"""Text-to-image search over precomputed CLIP embeddings.

Public API:
    search_by_text(query, threshold=...) -> (ranked_ids, scores)

Reads embeddings.npy + ids.json (row-aligned) which are produced by feature_engineering.py.
"""

import os
import sys
import json
import numpy as np
import torch
import torch.nn.functional as F
import clip

try:
    from src import config
    _DATA_DIR = config.DATA_DIR
except Exception:
    _DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dataset', 'data')

DEFAULT_EMBEDDINGS_PATH = os.path.join(_DATA_DIR, 'embeddings.npy')
DEFAULT_IDS_PATH = os.path.join(_DATA_DIR, 'ids.json')
DEFAULT_MODEL = 'ViT-L/14'
DEFAULT_THRESHOLD = 0.25

_model_cache = {}


def _get_clip_model(model_name, device):
    key = (model_name, device)
    if key not in _model_cache:
        model, _ = clip.load(model_name, device=device)
        model.eval()
        _model_cache[key] = model
    return _model_cache[key]


def load_embeddings(embeddings_path=DEFAULT_EMBEDDINGS_PATH, ids_path=DEFAULT_IDS_PATH):
    embeddings = np.load(embeddings_path)
    with open(ids_path) as f:
        ids = json.load(f)
    return ids, embeddings


def search_by_text(query, model_name=DEFAULT_MODEL, threshold=DEFAULT_THRESHOLD,
                   device=None, embeddings_path=DEFAULT_EMBEDDINGS_PATH,
                   ids_path=DEFAULT_IDS_PATH):
    device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
    ids, embeddings = load_embeddings(embeddings_path, ids_path)
    model = _get_clip_model(model_name, device)

    with torch.no_grad():
        tokens = clip.tokenize([query], truncate=True).to(device)
        q = F.normalize(model.encode_text(tokens), dim=-1).float().cpu().numpy()[0]

    scores = embeddings @ q
    idxs = np.where(scores >= threshold)[0]
    order = idxs[np.argsort(-scores[idxs])]
    ranked_ids = [ids[i] for i in order]
    ranked_scores = [float(scores[i]) for i in order]
    return ranked_ids, ranked_scores


if __name__ == '__main__':
    query = sys.argv[1] if len(sys.argv) > 1 else "impressionist painting"
    threshold = float(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_THRESHOLD
    ids, scores = search_by_text(query, threshold=threshold)
    print(f"Found {len(ids)} matches above threshold {threshold} for '{query}'")
    for aid, s in list(zip(ids, scores))[:20]:
        print(f"{aid}\t{s:.3f}")
