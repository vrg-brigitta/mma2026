import dash.dcc
from dash import html, dcc
from src.widgets import graph, heatmap, histogram, gallery, wordcloud, image_generator
from src.Dataset import Dataset
import dash_bootstrap_components as dbc

def generate_agent_widget():
    wordcloud_widget = wordcloud.create_wordcloud()
    gallery_widget = gallery.create_gallery()
    #graph_widget = graph.create_graph()
    #heatmap_widget = heatmap.create_heatmap()
    histogram_widget = histogram.create_histogram()
    image_generator_widget = image_generator.generate_image_generator_widget()

    tabs = dcc.Tabs([
        dcc.Tab(label='Images', children=gallery_widget),
        dcc.Tab(label='Genres', children=wordcloud_widget),
        dcc.Tab(label='Frequency', children=histogram_widget),
        #dcc.Tab(label='Graph', children=graph_widget),
        #dcc.Tab(label='Heatmap', children=heatmap_widget),
        dcc.Tab(label='Image Generator', children=image_generator_widget),
    ])

    return dbc.Stack([
        html.H5('Ask a question:'),

        dbc.Textarea(id='exploration-prompt', placeholder='Show me artworks that depict grief'),

        html.Div([
            dbc.Button("Submit", id="explore-button", color="primary"),
        ], className='d-grid mb-3'),

        tabs

    ], className='agent-container border-widget')
