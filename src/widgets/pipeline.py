import dash.dcc
from dash import html, dcc
from src.Dataset import Dataset
import dash_bootstrap_components as dbc

from src.widgets.projection_radio_buttons import create_projection_radio_buttons


def create_pipeline_widget():
    projection_radio_buttons = create_projection_radio_buttons();

    return dbc.Stack([
        html.H5('Steps taken to process data and generate insights'),
        html.Div(id='pipeline-steps'),
        projection_radio_buttons,
        html.H5('Prompt'),
        dash.dcc.Textarea(id='pipeline-prompt'),
        dbc.Stack([
            html.Button("Generate pipeline", id="generate-pipeline-button", className="btn btn-outline-primary")
        ],
            direction="horizontal",
            gap=2,
            className="agent-buttons"
        ),

        dcc.Loading(
            type="circle",
            children=html.Div(html.Img(id="generated-pipeline"), className='generated-pipeline-container')
        ),
    ], className='agent-container border-widget')