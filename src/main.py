import sys
from pathlib import Path

# Add parent directory to path to allow importing src module
sys.path.insert(0, str(Path(__file__).parent.parent))

from dash import Dash, html, dcc
from src import config
from src.Dataset import Dataset
from src.widgets import scatterplot, explore
import dash_bootstrap_components as dbc
from src.llm_handlers.query_handler import query_handler
from src.llm_handlers.clip_handler import clip_handler

# Need to import callbacks to register them,
# even if they are not used directly in this file.
import callbacks.scatterplot
import callbacks.search
import callbacks.describe

def run_ui():
    external_stylesheets = [dbc.themes.BOOTSTRAP]
    app = Dash(__name__, external_stylesheets=external_stylesheets)

    scatterplot_widget = scatterplot.create_scatterplot(config.DEFAULT_PROJECTION)

    explore_tab_widget = explore.create_explore_tab_widget()

    right_tab = dcc.Tabs([
        dcc.Tab(label='Explore', children=explore_tab_widget),
    ])

    app.layout = dbc.Container([
        dbc.Row([
            dbc.Col(scatterplot_widget, width=8, className='main-col'),
            dbc.Col(right_tab, width=4, className='main-col')
        ], justify='between', className='main-row'),
    ], fluid=True, id='container', className='app-container')

    app.run(debug=False, use_reloader=False, dev_tools_hot_reload=False)


def main():
    if not Dataset.files_exist():
        print('Missing one of the following dataset paths:')
        print('-', config.AUGMENTED_DATASET_PATH)
        print('-', config.DB_PATH)
        print('-', config.IMAGES_DIR)
        print('Creating augmented dataset.')
        Dataset.download()

    Dataset.load()

    if config.DATASET_SAMPLE_SIZE and len(Dataset.get()) != config.DATASET_SAMPLE_SIZE:
        print('Sample size changed in the configuration. Recalculating features.')
        Dataset.download()
        Dataset.load()

    
    clip_handler.load_embeddings()

    print('Starting Dash')
    run_ui()


if __name__ == '__main__':
    main()
