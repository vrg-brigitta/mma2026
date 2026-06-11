import sqlite3
import os

import pandas

from src import config, feature_engineering
from src.dataloaders import art_dataset_loader
from src.dataloaders.art_dataset_loader import DB_FILE_PATH

class DataBase:
    def __init__(self) -> None:
        self.sql_file = DB_FILE_PATH

    @staticmethod
    def connect_to_db(func):
        def wrapper(*args, **kw):
            self = args[0]
            with sqlite3.connect(self.sql_file) as self.con:
                return func(*args, **kw)
        return wrapper
    
    @connect_to_db
    def get_all(self, tb_name) -> list:
        cur = self.con.cursor()
        cur.execute('SELECT * FROM {};'.format(tb_name))
        return cur.fetchall()
    
    @connect_to_db
    def get_images_with_artwork_info(self) -> list:
        cur = self.con.cursor()
        cur.execute('SELECT * FROM Image_Info LEFT JOIN Artworks ON Image_Info.id = Artworks.image_info_id;')
        return cur.fetchall()


class Dataset:
    data = None
    count = None
    attr_data = None
    @staticmethod
    def load():
        Dataset.data = pandas.read_csv(config.AUGMENTED_DATASET_PATH, index_col='id')
        print('Dataset loaded with', len(Dataset.data), 'rows')

        Dataset.count = Dataset.data['genre'].value_counts()

        # db = DataBase()
        # artworks_columns = ('id', 'title', 'description', 'culture', 'period', 'dynasty', 'reign', 'type', 'genre', 'style', 'object_date', 'object_begin_date', 'object_end_date', 'location', 'medium', 'dataset_id', 'object_info_id', 'image_info_id',  'reference_date', 'reference_country', 'reference_region', 'preprocessed_description')
        # attributes = pandas.DataFrame(db.get_all('Artworks'), columns=artworks_columns)
        Dataset.attr_data = Dataset.data # data already contains all the attributes from Artworks table

        # TODO: append artist info (as attributes) too

    @staticmethod
    def get():
        return Dataset.data
    
    @staticmethod
    def get_attr_data():
        return Dataset.attr_data

    @staticmethod
    def class_count():
        return Dataset.count

    @staticmethod
    def files_exist():
        return os.path.isfile(DB_FILE_PATH) and os.path.isdir(config.IMAGES_DIR) and os.path.isfile(config.AUGMENTED_DATASET_PATH)

    @staticmethod
    def download():
        db = DataBase()
        image_info_columns = ('id', 'primary_image', 'additional_images', 'num_additional_images', 'alt_primary_image', 'file_path')
        artworks_columns = ('artwork_id', 'title', 'description', 'culture', 'period', 'dynasty', 'reign', 'type', 'genre', 'style', 'object_date', 'object_begin_date', 'object_end_date', 'location', 'medium', 'dataset_id', 'object_info_id', 'image_info_id',  'reference_date', 'reference_country', 'reference_region', 'preprocessed_description')

        original_data = pandas.DataFrame(db.get_images_with_artwork_info(), columns=image_info_columns + artworks_columns)
        print(original_data.head(2))
        # art_dataset_loader.load()
        feature_engineering.generate_projection_data(original_data)
        # art_dataset_loader.cleanup()
