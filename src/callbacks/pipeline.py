from dash import callback, Input, Output, State, ctx, html
from dash.exceptions import PreventUpdate
from threading import Thread
import uuid
import time


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

RUNNING_JOBS = {}


def _pipeline_job(job_id):
    global RUNNING_JOBS
    try:
        for i, step in enumerate(PIPELINE_STEPS):
            RUNNING_JOBS[job_id]["current_step"] = i
            step["fn"]()
            RUNNING_JOBS[job_id]["completed"].append(i)

        RUNNING_JOBS[job_id]["status"] = "finished"
    except Exception as e:
        RUNNING_JOBS[job_id]["status"] = "failed"
        print(f"Job {job_id} encountered an error: {e}")


@callback(
    Output("pipeline-run-store", "data"),
    Output("visualize-btn", "disabled"),
    Output("ui-tick", "disabled"),
    Input("visualize-btn", "n_clicks"),
    Input("ui-tick", "n_intervals"),
    State("pipeline-run-store", "data"),
    prevent_initial_call=True
)
def pipeline_step(n_clicks, n_intervals, store_data):
    trigger = ctx.triggered_id

    if trigger == "visualize-btn":
        job_id = str(uuid.uuid4())

        RUNNING_JOBS[job_id] = {
            "current_step": 0,
            "completed": [],
            "status": "running"
        }

        Thread(target=_pipeline_job, args=(job_id,), daemon=True).start()

        init_store = {
            "job_id": job_id,
            "running": True,
            "current_step": 0,
            "completed": [],
        }

        return init_store, True, False

    if trigger == "ui-tick":
        if not store_data or not store_data.get("running"):
            return store_data, False, True

        job_id = store_data.get("job_id")
        if not job_id or job_id not in RUNNING_JOBS:
            store_data["running"] = False
            return store_data, False, True

        job_info = RUNNING_JOBS[job_id]

        store_data["current_step"] = job_info["current_step"]
        store_data["completed"] = job_info["completed"]

        if job_info["status"] in ["finished", "failed"]:
            store_data["running"] = False
            del RUNNING_JOBS[job_id]
            return store_data, False, True

        return store_data, True, False

    raise PreventUpdate


@callback(
    Output("pipeline-builder-steps", "children"),
    Input("pipeline-run-store", "data")
)
def render_pipeline(store_data):
    # Don't render anything when no job has been started
    if not store_data or "job_id" not in store_data:
        return None

    # Once a job_id exists, extract the progress states
    current = store_data.get("current_step", 0)
    completed = set(store_data.get("completed", []))
    running = store_data.get("running", False)

    children = []

    for i, step in enumerate(PIPELINE_STEPS):
        if i in completed:
            circle_classnames = "pipeline-circle completed"
        elif i == current and running:
            circle_classnames = "pipeline-circle running"
        else:
            circle_classnames = "pipeline-circle"

        children.append(
            html.Div(
                [
                    html.Div(className=circle_classnames),
                    html.Div(step["label"], className="pipeline-label"),
                ],
                className="pipeline-step"
            )
        )

    return html.Div(children, className="pipeline-container")
