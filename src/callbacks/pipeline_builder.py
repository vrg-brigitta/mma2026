from dash import Input, Output, State, callback, html
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import json

# This defines the allowed next action in the pipeline based on the last action.

# The structure is a mapping from the last action type to a list of tuples,
# where each tuple contains the next action's value and its display label.
#
# Example:
#   "prev_block_type": [
#       "next_block_type"
#       [
#           ("value_1", "Label 1"),
#           ("value_2", "Label 2"),
#           ...
#       ]
#   ]
PIPELINE_OPTIONS = {
    "init": [
        "load",
        [
            ("input", "Load Dataset: Rijksmuseum"),
            ("input", "Load Dataset: MET"),
        ],
    ],

    "load": [
        "preprocess",
        [
            ("preprocess_32x32", "Preprocess: resize to 32x32"),
        ]
    ],

    "preprocess": [
        "embed",
        [
            ("clip_embeds", "Extract Embeddings: CLIP"),
            ("dino_embeds", "Extract Embeddings: DINOv2"),
        ]
    ],

    "embed": [
        "cluster",
        [
            ("cluster_umap", "Group Images: UMAP"),
            ("cluster_tsne", "Group Images: t-SNE"),
        ]
    ]
}


@callback(
    Output("pipeline-action-dropdown", "options"),
    Input("pipeline-builder-store", "data"),
)
def update_action_options(blocks):
    """
    Updates the dropdown options based on the store's current state.
    The user can only select actions that follow the last step in the pipeline.
    """
    prev_type = blocks[-1]["type"] if blocks else "init"
    options = PIPELINE_OPTIONS.get(prev_type, [])

    if len(options) == 0:
        return []

    return [
        {
            "label": label,
            "value": json.dumps({
                "type": options[0],
                "value": value,
                "label": label,
            })
        }
        for value, label in options[1]
    ]


@callback(
    Output("add-pipeline-action-btn", "disabled"),
    Input("pipeline-action-dropdown", "value")
)
def toggle_add_button(selected_value):
    """
    Disabled the "Add to current pipeline" button if
    no action is selected in the dropdown.
    """
    return not bool(selected_value)


@callback(
    Output("pipeline-action-dropdown", "disabled"),
    Input("pipeline-action-dropdown", "options")
)
def toggle_dropdown_disabled(options):
    """
    Disables the dropdown if there are no options available, which happens when
    the pipeline is complete and there are no next steps defined.
    """
    return not options


@callback(
    Output("pipeline-builder-store", "data", allow_duplicate=True),
    Output("pipeline-action-dropdown", "value", allow_duplicate=True),
    Input("add-pipeline-action-btn", "n_clicks"),
    State("pipeline-builder-store", "data"),
    State("pipeline-action-dropdown", "value"),
    prevent_initial_call=True
)
def add_step(_, blocks, selected_action_json):
    """
    This handles adding a step and clearing the dropdown selection.
    """
    if not selected_action_json:
        raise PreventUpdate

    blocks = blocks or []

    action_data = json.loads(selected_action_json)

    blocks = list(blocks)  # avoid mutating the state
    blocks.append({
        "type": action_data["type"],
        "value": action_data["value"],
        "label": action_data["label"]
    })

    return blocks, None


@callback(
    Output("pipeline-builder-store", "data", allow_duplicate=True),
    Output("pipeline-action-dropdown", "value", allow_duplicate=True),
    Input("clear-pipeline-btn", "n_clicks"),
    prevent_initial_call=True
)
def clear_pipeline(_):
    """
    Clear the pipeline by resetting the store and the dropdown selection.
    """
    return [], None


@callback(
    Output("clear-pipeline-btn", "disabled"),
    Input("pipeline-builder-store", "data")
)
def toggle_clear_disabled(blocks):
    """
    Disables the "Clear" button if there are no steps in the pipeline.
    """
    return not bool(blocks)


@callback(
    Output("generate-pipeline-btn", "disabled"),
    Input("pipeline-prompt", "value")
)
def toggle_generate_button(text):
    """
    Disables the "Generate Pipeline" button if the prompt is empty.
    """
    return not bool(text and text.strip())


@callback(
    Output("pipeline-builder-steps", "children"),
    Input("pipeline-builder-store", "data")
)
def render_pipeline(blocks):
    """
    This renders the visual flow UI.
    """
    children = []
    blocks = blocks or []

    for i, step in enumerate(blocks):
        children.append(
            html.Div(
                [
                    html.Div(className="pipeline-circle"),
                    html.Div(step["label"], className="pipeline-label"),
                ],
                className="pipeline-step"
            )
        )

    return html.Div(children, className="pipeline-container")
