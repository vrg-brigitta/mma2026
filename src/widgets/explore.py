import dash.dcc
from dash import html, dcc
import dash_bootstrap_components as dbc


def create_explore_tab_widget():
    return dbc.Stack([
        dbc.Stack([
            # =============================================
            # Ask a question
            # =============================================
            html.H5("Ask a question"),
            html.P("Ask about the selected or visible data on the canvas."),
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
            dcc.Store(id="result-img-clicks-tracker-store", data={}),

            html.Hr(),

            # =============================================
            # Describe
            # =============================================
            dbc.Stack([
                html.H5("Describe"),
                html.P("Describe the selected or visible data on the canvas. At most 200 (random) images will be described."),
                dbc.Stack([
                    html.Button(
                        "Describe data",
                        id="describe-btn",
                        className="btn btn-outline-primary",
                    ),
                ], direction="horizontal", gap=2),
            ], direction="vertical", className="describe-results sidebar-group"),

            dcc.Store(id="describe-trigger-store"),

            html.Hr(),

            # =============================================
            # Results
            # =============================================
            dbc.Stack([
                html.H5("Results"),
                html.Div(html.P("Ask a question or describe the data you're interested in."), id="results-summary"),
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

        # =============================================
        # Modal for image preview
        # =============================================
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Artwork Detail View"), close_button=True),
            dbc.ModalBody(
                dbc.Row([
                    dbc.Col(
                        html.Img(id="modal-preview-img", className="modal-preview-image"),
                        md=7, 
                        className="modal-image-col text-center"
                    ),

                    dbc.Col([                      
                        html.Div(id="modal-metadata-container", className="modal-metadata-scroll"),
                        
                        html.Button(
                            "Show on Canvas",
                            id="show-on-canvas-btn",
                            className="btn btn-success btn-lg w-100 modal-action-btn",
                            n_clicks=0
                        )
                    ], md=5, className="modal-details-col")
                ], className="modal-body-row")
            ),
            dcc.Store(id="active-modal-artwork-id")
        ], id="image-preview-modal", size="xl", centered=True, className="image-preview-modal")
    ], className="sidebar-container border-widget")
