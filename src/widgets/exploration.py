import dash.dcc
from dash import html, dcc
from src.widgets import graph, heatmap, histogram, gallery, wordcloud
from src.Dataset import Dataset
import dash_bootstrap_components as dbc

def generate_agent_widget():
    wordcloud_widget = wordcloud.create_wordcloud()
    gallery_widget = gallery.create_gallery()
    graph_widget = graph.create_graph()
    heatmap_widget = heatmap.create_heatmap()
    histogram_widget = histogram.create_histogram()

    tabs = dcc.Tabs([
        dcc.Tab(label='wordcloud', children=wordcloud_widget),
        dcc.Tab(label='images', children=gallery_widget),
        dcc.Tab(label='histogram', children=histogram_widget),
        dcc.Tab(label='graph', children=graph_widget),
        dcc.Tab(label='heatmap', children=heatmap_widget),
    ])

    return dbc.Stack([
        html.H5('Top 10 characteristics'),
        html.Div(id='characteristics-description'),
        html.H5('Prompt'),
        dash.dcc.Textarea(id='prompt'),
        dbc.Stack([
            html.Button("Generate prompt", id="generate-prompt-button", className="btn btn-outline-primary"),
            html.Button("Generate image", id="generate-image-button", className="btn btn-outline-primary")
        ],
            direction="horizontal",
            gap=2,
            className="agent-buttons"
        ),

        dcc.Loading(
            type="circle",
            children=html.Div(html.Img(id="generated-image"), className='generated-image-container')
        ),

        tabs

    ], className='agent-container border-widget')

def get_top_characteristics(selected_data):
    if selected_data is None or selected_data.empty:
        return []

    attr_data = Dataset.get_attr_data().loc[selected_data.index]

    characteristics = []
    for col in attr_data.columns:
        if col == 'num_additional_images':
            continue

        counts = attr_data[col].value_counts(dropna=True)
        duplicate_counts = counts[counts > 1]
        duplicate_rows = int(duplicate_counts.sum())
        if duplicate_rows > 0:
            top_shared_value = duplicate_counts.idxmax()
            characteristics.append((col, top_shared_value, duplicate_rows))

    top_characteristics = sorted(
        characteristics,
        key=lambda item: item[2],
        reverse=True
    )[:10]

    return [html.P(f"{col}: {value}")
            for col, value, count in top_characteristics]