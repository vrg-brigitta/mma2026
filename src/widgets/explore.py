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

            dbc.Stack([
                html.Button(
                    "Submit",
                    id="submit-question-btn",
                    className="btn btn-primary mt-2",
                ),

                html.Div(id="pipeline-status-container", className="mt-2"),
            ], direction="horizontal", gap=2),

            dcc.Interval(
                id="ui-tick",
                interval=1000,
                n_intervals=0,
                disabled=True
            ),

            dcc.Store(
                id="pipeline-run-store",
                data={}
            ),

            html.Hr(),

            dbc.Stack([
                html.H5("Describe"),
                html.P("Click on the button below to describe the data that is visible in the canvas."),
                dbc.Stack([
                    html.Button(
                        "Submit",
                        id="describe-btn",
                        className="btn btn-outline-primary",
                    ),
                ], direction="horizontal", gap=2),
            ], direction="vertical", className="explore-results"),

            html.Hr(),

            dbc.Stack([
                html.H5("Results"),
                html.P("Found 9318 images that may depict grief. Among these, 7882 (84.6%) are related to Asian cultures."),
                dbc.Stack([
                    html.Div(html.Img(src="https://picsum.photos/200/300"), className="explore-results-item"),
                    html.Div(html.Img(src="https://picsum.photos/200/300"), className="explore-results-item"),
                    html.Div(html.Img(src="https://picsum.photos/200/300"), className="explore-results-item"),
                    html.Div(html.Img(src="https://picsum.photos/200/300"), className="explore-results-item"),
                    html.Div(html.Img(src="https://picsum.photos/200/300"), className="explore-results-item"),
                    html.Div(html.Img(src="https://picsum.photos/200/300"), className="explore-results-item"),
                ], className="explore-results-grid")
            ], direction="vertical", className="explore-results"),

        ]),
    ], className="sidebar-container border-widget")
