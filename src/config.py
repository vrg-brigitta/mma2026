import os
from pathlib import Path
import torch


DEVICE = 'cuda' if torch.cuda.is_available() else ('mps' if torch.backends.mps.is_available() else 'cpu')

# ui configuration
IMAGE_GALLERY_SIZE = 24
IMAGE_GALLERY_ROW_SIZE = 4

WORDCLOUD_IMAGE_HEIGHT = 600
WORDCLOUD_IMAGE_WIDTH = 800

SCATTERPLOT_COLOR = 'rgba(31, 119, 180, 0.5)'
SCATTERPLOT_SELECTED_COLOR = 'rgba(255, 0, 0, 0.5)'

# When the viewport span (max of x/y range) is <= this value, images are shown
# Larger spans are considered 'zoomed out' and images are hidden.
SCATTERPLOT_IMAGE_ZOOM_THRESHOLD = 5.0

MAX_IMAGES_ON_SCATTERPLOT = 100
MAX_EXPLORE_RESULTS_IMAGES_PER_PAGE = 10

DESCRIBE_MAX_POINTS = 500

DEFAULT_PROJECTION = 'UMAP'
DEFAULT_LEFT_WIDGET = 'table'

GENERATED_IMAGE_SIZE = (200, 300)

# dataset extraction configuration
DATASET_SAMPLE_SIZE = None # number of images in the CUB-200-2011 dataset is 11788, that is the max value for this parameter
# 889868 is the number of images in the Art Dataset
RANDOM_SAMPLING = False # if false, the first DATASET_SAMPLE_SIZE images will be taken, otherwise a random sample of size DATASET_SAMPLE_SIZE will be taken
FILTER_NON_NULL_COLUMNS = True

CLIP_MODEL = 'ViT-L/14'
CLIP_THRESHOLD = 0.3
CLIP_EMBEDS_BATCH_SIZE = 256

# path configuration
ROOT_DIR = Path(__file__).parent.parent
DATASET_DIR = os.path.join(ROOT_DIR, 'dataset')
DATA_DIR = os.path.join(DATASET_DIR, 'data')
DOWNLOADS_DIR = os.path.join(DATASET_DIR, 'downloads')
DATASET_PATH = os.path.join(DATA_DIR, 'dataset.csv')
IMAGES_DIR = os.path.join(DATA_DIR, 'images')
AUGMENTED_DATASET_PATH = os.path.join(DATA_DIR, 'augmented_dataset.csv')
ATTRIBUTE_DATA_PATH = os.path.join(DATA_DIR, 'image_attributes.csv')
EMBEDDINGS_PATH = os.path.join(DATA_DIR, 'embeddings.npy')
IDS_PATH = os.path.join(DATA_DIR, 'ids.json')
UMAP_REDUCER_PATH = os.path.join(DATA_DIR, 'umap_reducer.pkl')
DB_PATH = os.path.join(DOWNLOADS_DIR, 'vagen_database_MMA.db')