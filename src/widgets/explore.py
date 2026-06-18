import dash.dcc
from dash import html, dcc
import dash_bootstrap_components as dbc


def create_explore_tab_widget():
    return dbc.Stack([
        dbc.Stack([
            html.H5("Ask a question"),
            dash.dcc.Textarea(
                id="question-input",
                placeholder="An old Japanese woodblock print of waves",
                className="question-input",
            ),

            dbc.Stack([
                html.Button(
                    html.Span("Submit", id="submit-btn-label"),
                    id="submit-question-btn",
                    className="btn btn-primary mt-2",
                    disabled=True,
                ),

                html.Div(id="pipeline-status-container", className="mt-2"),
            ], direction="horizontal", gap=2),

            dcc.Interval(
                id="ui-tick",
                interval=1000,
                n_intervals=0,
                disabled=True
            ),

            dcc.Store(id="search-trigger-store"),
            dcc.Store(id="load-more-trigger-store"),
            dcc.Store(id="search-state-store", data={"all_ids": [], "offset": 0}),

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
            ], direction="vertical", className="describe-results sidebar-group"),

            html.Hr(),

            dbc.Stack([
                html.H5("Results"),
                html.P("Ask a question or describe the data you're interested in.", id="results-summary"),
                html.Div(
                    dcc.Loading(children=dbc.Stack(id="explore-results-grid", className="explore-results-grid")),
                    className="explore-results-inner-container"
                ),
                dbc.Stack([
                    html.Button(
                        "Load more results",
                        id="load-more-btn",
                        className="btn btn-outline-secondary mt-2",
                        style={"display": "none"}
                    ),
                ], direction="horizontal", gap=2, className="load-more-btn-container"),
            ], direction="vertical", className="explore-results-container sidebar-group"),
            html.Div(id="scroll-dummy", style={"display": "none"}),
        ]),

        # Model for image preview
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Image Preview"), close_button=True),
            dbc.ModalBody(
                html.Div([
                    html.Img(id="modal-preview-img")
                ], className="text-center")
            ),
        ], id="image-preview-modal", className="image-preview-modal", size="xl", centered=True)
    ], className="sidebar-container border-widget")
