import sqlite3
import os
import time

import pandas

from src import config, feature_engineering
from src.dataloaders import art_dataset_loader

class DataBase:
    def __init__(self) -> None:
        self.sql_file = config.DB_PATH

    @staticmethod
    def connect_to_db(func):
        def wrapper(*args, **kw):
            self = args[0]
            with sqlite3.connect(self.sql_file) as self.con:
                return func(*args, **kw)
        return wrapper
    
    @connect_to_db
    def get_all(self, tb_name) -> list:
        df = pandas.read_sql('SELECT * FROM {};'.format(tb_name), self.con)
        return df
    
    @connect_to_db
    def get_artworks_with_imageinfo(self) -> pandas.DataFrame:
        df = pandas.read_sql("""
            SELECT
                a.id AS id,
                i.file_path,
                i.primary_image,
                i.alt_primary_image,
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
            WHERE i.file_path IS NOT NULL""" 
            + """ AND a.culture IS NOT NULL
                AND a.period IS NOT NULL
                AND a.type IS NOT NULL
                AND a.genre IS NOT NULL
                AND a.description IS NOT NULL
              """ if config.FILTER_NON_NULL_COLUMNS else "", 
            self.con)
        
        return df


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
        return os.path.isfile(config.DB_PATH) and os.path.isdir(config.IMAGES_DIR) and os.path.isfile(config.AUGMENTED_DATASET_PATH)

    @staticmethod
    def download():
        db = DataBase()
        df = db.get_artworks_with_imageinfo()

        if config.RANDOM_SAMPLING:
            df = df.sample(n=config.DATASET_SAMPLE_SIZE, random_state=1) if config.DATASET_SAMPLE_SIZE else df
        else:
            df = df.head(config.DATASET_SAMPLE_SIZE) if config.DATASET_SAMPLE_SIZE else df

        images_to_load = list(df[['id', 'file_path']].itertuples(index=False, name=None))

        art_dataset_loader.load(images_to_load)
        feature_engineering.generate_projection_data(df)

        #art_dataset_loader.cleanup()

    @staticmethod
    def get_image_url(artwork_id):
        try:
            artwork_id = int(artwork_id)
            return Dataset.data.loc[artwork_id, "file_path"]
        except (KeyError, ValueError, TypeError):
            return None
