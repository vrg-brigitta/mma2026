import dash.dcc
from dash import html, dcc
from src.Dataset import Dataset
import dash_bootstrap_components as dbc

def generate_image_generator_widget():
    return dbc.Stack([
        # html.H5('Top 10 characteristics'),
        html.Div(id='characteristics-description', hidden = True),
        html.H5('Describe the image you want to generate'),
        dash.dcc.Textarea(id='image-generator-prompt'),
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
    ], className='sidebar-container border-widget')

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
