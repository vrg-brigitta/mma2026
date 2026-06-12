import dash.dcc
from dash import html, dcc
import dash_bootstrap_components as dbc

from src.widgets.pipeline_builder import create_pipeline_builder


def create_pipeline_tab_widget():
    pipeline_builder = create_pipeline_builder()

    return dbc.Stack([
        dbc.Stack([
            html.Div(
                [
                    html.H5("Current pipeline"),
                    html.Button(
                        "Clear",
                        id="clear-pipeline-btn",
                        className="btn clear-pipeline-btn btn-sm btn-outline-danger"
                    ),
                ],
                className="d-flex justify-content-between align-items-center"
            ),
            html.Div(id="pipeline-steps"),
            pipeline_builder,

            html.Hr(),

            html.H5("Generate pipeline"),
            dash.dcc.Textarea(
                id="pipeline-prompt",
                placeholder="I want to examine which themes are in this dataset",
                style={"width": "100%", "height": 100},
            ),
            html.Button(
                "Start generation",
                id="generate-pipeline-btn",
                className="btn btn-outline-primary mt-2",
                disabled=True,
            )
        ]),
        html.Button(
            "Visualize",
            id="visualize-btn",
            className="btn btn-primary"
        ),

        # dcc.Loading(
        #     type="circle",
        #     children=html.Div(
        #         html.Img(id="generated-pipeline"),
        #         className="generated-pipeline-container"
        #     )
        # ),
    ], className="sidebar-container border-widget")
