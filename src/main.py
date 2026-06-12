import sys
from pathlib import Path

# Add parent directory to path to allow importing src module
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.dataloaders.art_dataset_loader import DB_FILE_PATH

from dash import Dash, html, dcc
from src import config
from src.Dataset import Dataset
from src.widgets import projection_radio_buttons, gallery, scatterplot, wordcloud, graph, heatmap, histogram, help_popup, pipeline
from src.widgets.table import create_table
from src.widgets import exploration
import dash_bootstrap_components as dbc

# need to import callbacks to register them, even if they are not used directly in this file
import callbacks.table
import callbacks.scatterplot
import callbacks.projection_radio_buttons
#import callbacks.heatmap
import callbacks.wordcloud
import callbacks.histogram
import callbacks.gallery
#import callbacks.graph
import callbacks.exploration
import callbacks.image_generator
import callbacks.pipeline_builder

def run_ui():
    external_stylesheets = [dbc.themes.BOOTSTRAP]
    app = Dash(__name__, external_stylesheets=external_stylesheets)

    help_popup_widget = help_popup.create_help_popup()
    scatterplot_widget = scatterplot.create_scatterplot(config.DEFAULT_PROJECTION)

    pipeline_tab_widget = pipeline.create_pipeline_tab_widget()
    explore_tab_widget = exploration.create_explore_tab_widget()

    table_widget = create_table()

    right_tab = dcc.Tabs([
        dcc.Tab(label='Pipeline', children=pipeline_tab_widget),
        dcc.Tab(label='Explore', children=explore_tab_widget),
    ])

    app.layout = dbc.Container([
        help_popup_widget,
        dbc.Stack([
            dbc.Label('Art Exploration Dashboard', className='header-title'),
            # dbc.Button('Deselect everything', id='deselect-button', class_name="btn btn-outline-primary ms-auto header-button"),
            # dbc.Button('Help', id='help-button', class_name="btn btn-outline-primary header-button")
        ], id='header', direction="horizontal"),
        dbc.Row([
            dbc.Col(scatterplot_widget, width=8, className='main-col'),
            dbc.Col(right_tab, width=4, className='main-col')],
            justify='between', className='main-row'),
        dbc.Row([
            dbc.Col(table_widget, className='main-col')
        ], className='hidden-row')
    ], fluid=True, id='container')

    app.run(debug=True, use_reloader=False)


def main():
    if not Dataset.files_exist():
        print('Missing one of the following dataset paths:')
        print('-', config.AUGMENTED_DATASET_PATH)
        print('-', DB_FILE_PATH)
        print('-', config.IMAGES_DIR)
        print('Creating dataset.')
        Dataset.download()

    Dataset.load()

    if len(Dataset.get()) != config.DATASET_SAMPLE_SIZE:
        print('Sample size changed in the configuration. Recalculating features.')
        Dataset.download()
        Dataset.load()

    print('Starting Dash')
    run_ui()


if __name__ == '__main__':
    main()
