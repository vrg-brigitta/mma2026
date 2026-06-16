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


# Define a sequence of steps that show the progress of the pipeline.
PIPELINE_STEPS = [
    {"label": "Loading dataset", "fn": load_dataset},
    {"label": "Resizing images", "fn": preprocess_nxn},
    {"label": "Extract embeddings", "fn": extract_embeddings},
    {"label": "Clustering", "fn": create_clusters},
]

# For now we'll keep track of running jobs in memory, but with millions of
# users this could become a bottleneck, but for now this is fine.
RUNNING_JOBS = {}


def _bg_pipeline_worker(job_id):
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
    Output("submit-question-btn", "disabled"),
    Output("ui-tick", "disabled"),
    Input("submit-question-btn", "n_clicks"),
    Input("ui-tick", "n_intervals"),
    State("pipeline-run-store", "data"),
    prevent_initial_call=True
)
def control_pipeline(n_clicks, n_intervals, store_data):
    trigger = ctx.triggered_id

    if trigger == "submit-question-btn":
        if n_clicks is None:
            raise PreventUpdate

        job_id = uuid.uuid4().hex
        RUNNING_JOBS[job_id] = {
            "current_step": 0,
            "completed": [],
            "status": "running"
        }
        Thread(target=_bg_pipeline_worker, args=(job_id,), daemon=True).start()

        return {
            "job_id": job_id,
            "running": True,
            "current_step": 0,
            "completed": []
        }, True, False

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
    Output("pipeline-status-container", "children"),
    Input("pipeline-run-store", "data")
)
def render_pipeline_status(store_data):
    # If store is empty or job hasn't started, render nothing.
    if not store_data or "job_id" not in store_data:
        return None

    current_step = store_data.get("current_step", 0)
    running = store_data.get("running", False)

    # Only render while the pipeline is actively running.
    if running:
        if current_step >= len(PIPELINE_STEPS):
            return None

        current_label = PIPELINE_STEPS[current_step]["label"]

        return html.Div(
            [
                html.Span(className="pipeline-status-spinner"),
                html.Span(current_label, className="pipeline-status-text")
            ],
            className="pipeline-status-inner-container"
        )

    # Render nothing when it's done.
    return None
