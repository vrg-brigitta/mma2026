import os
import os.path
from pathlib import Path
import sqlite3
import sys
import wget


# Add parent directory to path to allow importing src module
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from PIL import Image
from tqdm import tqdm

from src import config

DB_FILE_PATH = os.path.join(config.DOWNLOADS_DIR, 'vagen_database_MMA.db')
IMAGES_SIZE = (120, 120)

def resize_images(images_dir):
    for image_name in tqdm(os.listdir(images_dir)):
        image_path = os.path.join(images_dir, image_name)
        image = Image.open(image_path)
        image.thumbnail(IMAGES_SIZE)
        image.save(image_path)


def load():
    if not os.path.isdir(config.DATASET_DIR):
        os.mkdir(config.DATASET_DIR)
    if not os.path.isdir(config.DOWNLOADS_DIR):
        os.mkdir(config.DOWNLOADS_DIR)
    if not os.path.isfile(DB_FILE_PATH):
        print('Sqllite db not found at', DB_FILE_PATH)

    # downloading images

    with sqlite3.connect(DB_FILE_PATH) as con:
        cursor = con.cursor()
        cursor.execute('SELECT id, file_path FROM Image_Info')
        images = cursor.fetchall()

    for image in tqdm(images, desc='Downloading images'):
        id, file_path = image
        save_path = os.path.join(config.IMAGES_DIR, str(id) + '.jpg')
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        if not os.path.isfile(save_path):
            wget.download(file_path, save_path)

        if config.RANDOM_SAMPLING is False and id >= config.DATASET_SAMPLE_SIZE:
            break


def cleanup():
    print('Resizing images')
    resize_images(config.IMAGES_DIR)


if __name__ == '__main__':
    load()
    #cleanup()