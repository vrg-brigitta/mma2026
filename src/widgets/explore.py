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
                "Start generation",
                id="submit-question-btn",
                className="btn btn-outline-primary mt-2",
                disabled=True,
            ),

            html.Button(
                "Visualize",
                id="visualize-btn",
                className="btn btn-primary",
                disabled=False
            ),

            dcc.Interval(
                id="ui-tick",
                interval=200,
                n_intervals=0
            ),

            html.Div(id="pipeline-builder-steps"),

            dcc.Store(
                id="dummy-store"
            )
        ]),
    ], className="sidebar-container border-widget")
