import os

# This is needed to prevent numba from using multiple threads, which can cause
# issues on macOS. It is crucial to place it before all the other imports.
os.environ["NUMBA_NUM_THREADS"] = "1"

import json
import sqlite3
import joblib
import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
import clip
from PIL import Image
from tqdm import tqdm
from umap import UMAP
from sklearn.manifold import TSNE

from src import config


def load_metadata():
    con = sqlite3.connect(config.DB_PATH)
    df = pd.read_sql("""
        SELECT
            a.id AS id,
            i.file_path,
            a.title,
            a.description,
            a.culture,
            a.period,
            a.dynasty,
            a.reign,
            a.type,
            a.genre,
            a.style,
            a.object_date,
            a.object_begin_date,
            a.object_end_date,
            a.location,
            a.medium,
            a.reference_date,
            a.reference_country,
            a.reference_region,
            a.preprocessed_description
        FROM Artworks a
        JOIN Image_Info i ON i.id = a.image_info_id
        WHERE a.culture IS NOT NULL
          AND a.period IS NOT NULL
          AND a.type IS NOT NULL
          AND a.genre IS NOT NULL
          AND a.description IS NOT NULL
          AND i.file_path IS NOT NULL
    """, con)
    con.close()
    df = df.set_index('id')
    return df


def calculate_clip_embeddings(df):
    model, preprocess = clip.load(config.CLIP_MODEL, device=config.DEVICE)
    model.eval()

    all_embeddings = []
    ids = list(df.index)

    for i in tqdm(range(0, len(ids), config.CLIP_EMBEDS_BATCH_SIZE), desc='CLIP'):
        batch_ids = ids[i:i + config.CLIP_EMBEDS_BATCH_SIZE]
        imgs = []
        valid_ids = []
        for artwork_id in batch_ids:
            path = os.path.join(config.IMAGES_DIR, f"{artwork_id}.jpg")
            try:
                imgs.append(preprocess(Image.open(path).convert('RGB')))
                valid_ids.append(artwork_id)
            except Exception as e:
                print(f"  skip {artwork_id}: {e}", flush=True)

        if not imgs:
            continue

        batch = torch.stack(imgs).to(config.DEVICE)
        with torch.no_grad():
            feats = model.encode_image(batch)
            feats = F.normalize(feats, dim=-1).float().cpu().numpy()

        all_embeddings.append((valid_ids, feats))

    id_to_embed = {}
    for valid_ids, feats in all_embeddings:
        for aid, feat in zip(valid_ids, feats):
            id_to_embed[aid] = feat

    kept_ids = [aid for aid in ids if aid in id_to_embed]
    embeddings = np.stack([id_to_embed[aid] for aid in kept_ids])
    return kept_ids, embeddings


def calculate_umap(embeddings):
    reducer = UMAP(metric='cosine', n_components=2, random_state=42)
    coords = reducer.fit_transform(embeddings)
    return coords[:, 0], coords[:, 1], reducer


def calculate_tsne(embeddings):
    tsne = TSNE(metric='cosine', n_components=2, random_state=42)
    coords = tsne.fit_transform(embeddings)
    return coords[:, 0], coords[:, 1]


def generate_projection_data(original_data=None):
    os.makedirs(config.DATA_DIR, exist_ok=True)

    df = load_metadata()

    if config.RANDOM_SAMPLING:
        df = df.sample(n=config.DATASET_SAMPLE_SIZE, random_state=1) if config.DATASET_SAMPLE_SIZE else df
    else:
        df = df.head(config.DATASET_SAMPLE_SIZE) if config.DATASET_SAMPLE_SIZE else df

    print(f'Processing {len(df)} artworks on {config.DEVICE} with {config.CLIP_MODEL}')

    kept_ids, embeddings = calculate_clip_embeddings(df)
    df = df.loc[kept_ids]

    np.save(config.EMBEDDINGS_PATH, embeddings)
    with open(config.IDS_PATH, 'w') as f:
        json.dump([int(x) for x in kept_ids], f)

    umap_x, umap_y, reducer = calculate_umap(embeddings)
    joblib.dump(reducer, config.UMAP_REDUCER_PATH)

    tsne_x, tsne_y = calculate_tsne(embeddings)

    df = df.assign(umap_x=umap_x, umap_y=umap_y, tsne_x=tsne_x, tsne_y=tsne_y)
    df.to_csv(config.AUGMENTED_DATASET_PATH, index=True)

    print(f'Done. Embeddings shape: {embeddings.shape}')


if __name__ == '__main__':
    generate_projection_data()
