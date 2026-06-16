import dash.dcc
from dash import html, dcc
import dash_bootstrap_components as dbc


def create_explore_tab_widget():
    return dbc.Stack([
        dbc.Stack([
            html.H5("Ask a question"),
            dash.dcc.Textarea(
                id="question-input",
                placeholder="Show me all images of cats",
                style={"width": "100%", "height": 100},
            ),

            html.Button(
                "Visualize",
                id="visualize-btn",
                className="btn btn-primary",
                disabled=False
            ),

            dcc.Interval(
                id="ui-tick",
                interval=1000,
                n_intervals=0,
                disabled=True,
            ),

            html.Div(id="pipeline-builder-steps"),

            dcc.Store(
                id="pipeline-run-store",
                data={}
            ),
        ]),
    ], className="sidebar-container border-widget")
