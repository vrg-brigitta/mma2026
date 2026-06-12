from dash import html, dcc
import dash_bootstrap_components as dbc


def create_pipeline_builder():
    return html.Div([
        html.Div(id="pipeline-builder-steps"),
        dbc.Label("Add pipeline action"),
        dcc.Dropdown(
            id="pipeline-action-dropdown",
            placeholder="Select next action",
            searchable=False,
        ),
        html.Button(
            "Add to current pipeline",
            id="add-pipeline-action-btn",
            className="btn btn-outline-primary mt-2 w-100",
            disabled=True,
        ),
        dcc.Store(
            id="pipeline-builder-store",
            data=[]
        )
    ])
