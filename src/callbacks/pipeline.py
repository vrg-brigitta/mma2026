from dash import Dash, html, dcc, Input, Output, State, callback
import dash_bootstrap_components as dbc
from threading import Thread
import time

# =========================
# PIPELINE STEPS
# =========================


def load_dataset():
    print("Loading dataset...")
    time.sleep(2)
    print("Dataset loaded")


def preprocess_nxn():
    print("Preprocessing images...")
    time.sleep(3)
    print("Preprocessing done")


def extract_embeddings():
    print("Extracting embeddings...")
    time.sleep(4)
    print("Embeddings done")


def create_clusters():
    print("Clustering...")
    time.sleep(2)
    print("Clustering done")


PIPELINE_STEPS = [
    {"label": "Loading MET dataset", "fn": load_dataset},
    {"label": "Resizing images", "fn": preprocess_nxn},
    {"label": "Extract embeddings", "fn": extract_embeddings},
    {"label": "Clustering", "fn": create_clusters},
]

PIPELINE_STATE = {
    "running": False,
    "current_step": -1,
    "completed": []
}


def run_pipeline():
    global PIPELINE_STATE

    PIPELINE_STATE["running"] = True
    PIPELINE_STATE["current_step"] = 0
    PIPELINE_STATE["completed"] = []

    for i, step in enumerate(PIPELINE_STEPS):
        PIPELINE_STATE["current_step"] = i
        step["fn"]()
        PIPELINE_STATE["completed"].append(i)

    PIPELINE_STATE["running"] = False
    PIPELINE_STATE["current_step"] = len(PIPELINE_STEPS)

    print("done")


@callback(
    Output("visualize-btn", "disabled"),
    Input("visualize-btn", "n_clicks"),
    prevent_initial_call=True
)
def start(_):
    Thread(target=run_pipeline, daemon=True).start()
    return True


@callback(
    Output("pipeline-builder-steps", "children"),
    Input("ui-tick", "n_intervals")
)
def render(_):

    state = PIPELINE_STATE

    current = state["current_step"]
    completed = set(state["completed"])

    children = []

    for i, step in enumerate(PIPELINE_STEPS):

        if i in completed:
            cls = "pipeline-circle completed"
        elif i == current:
            cls = "pipeline-circle running"
        else:
            cls = "pipeline-circle"

        children.append(
            html.Div(
                [
                    html.Div(className=cls),
                    html.Div(step["label"], className="pipeline-label"),
                ],
                className="pipeline-step"
            )
        )

    return html.Div(children, className="pipeline-container")
