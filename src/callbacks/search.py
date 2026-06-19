import dash
from dash import callback, Input, Output, State, html, clientside_callback, ALL
from dash.exceptions import PreventUpdate

from src.llm_handlers.query_handler import query_handler
from src.llm_handlers.clip_handler import clip_handler
from src.Dataset import Dataset


# ==========================================
#  Invoke search on submit
# ==========================================

@callback(
    Output("submit-question-btn", "disabled", allow_duplicate=True),
    Input("question-input", "value"),
    State("submit-btn-label", "children"),
    prevent_initial_call=True,
)
def toggle_submit_disabled(value, current_label):
    """
    Disable the submit button if the input is empty.
    """
    if current_label == "Searching...":
        raise PreventUpdate

    is_empty = not value or not value.strip()
    return is_empty


@callback(
    Output("submit-question-btn", "disabled", allow_duplicate=True),
    Output("submit-btn-label", "children", allow_duplicate=True),
    Output("search-trigger-store", "data"),
    Input("submit-question-btn", "n_clicks"),
    prevent_initial_call=True,
)
def set_search_loading_state(n_clicks):
    """
    When the user clicks the submit button, we set it to a loading state and
    trigger the search.
    """
    if not n_clicks:
        raise PreventUpdate
    return True, "Searching...", n_clicks


@callback(
    Output("explore-results-grid", "children", allow_duplicate=True),
    Output("results-summary", "children", allow_duplicate=True),
    Output("submit-question-btn", "disabled", allow_duplicate=True),
    Output("submit-btn-label", "children", allow_duplicate=True),
    Output("search-state-store", "data"),
    Output("load-more-btn", "style", allow_duplicate=True),
    Output("load-more-btn", "disabled", allow_duplicate=True),
    Output("load-more-btn", "children", allow_duplicate=True),
    State("question-input", "value"),
    Input("search-trigger-store", "data"),
    prevent_initial_call=True,
)
def run_initial_search(user_query, store_data):
    """
    When the search trigger store is updated (by clicking the submit button),
    we run the search and update the results grid.
    """
    if not store_data or not user_query or not user_query.strip():
        raise PreventUpdate

    user_query = user_query.strip()
    query = query_handler.to_clip_query(user_query)

    submit_btn_disabled = False
    submit_btn_label = "Submit"
    hide_btn = {"display": "none"}
    empty_state = {"all_ids": [], "offset": 0}

    if query is None:
        return (
            html.Div("Could not understand the query.", className="text-danger"),
            html.P("Could not understand the query."),
            submit_btn_disabled, submit_btn_label, empty_state, hide_btn, True, "Load more results"
        )

    ids, scores = clip_handler.search_by_text(query)

    if not ids:
        return (
            html.Div("No results found.", className="text-warning"),
            html.P("No results found."),
            submit_btn_disabled, submit_btn_label, empty_state, hide_btn, True, "Load more results"
        )

    top_ids = ids[:10]
    images = [
        html.Div(
            html.Img(
                src=Dataset.get_image_url(artwork_id),
                # Use a dictionary ID for pattern-matching
                id={"type": "thumb-img", "index": artwork_id},
                n_clicks=0,
                style={"cursor": "pointer", "width": "100%"} # Pointer cursor indicates interactivity
            ),
            className="explore-results-item"
        )
        for artwork_id in top_ids
    ]

    has_more = len(ids) > len(images)
    load_more_style = {"display": "block"} if has_more else {"display": "none"}
    summary = html.P(f"Found {len(ids)} images. Displaying top {len(images)} results.")

    new_state = {"all_ids": ids, "offset": 10}

    return (
        images, summary, submit_btn_disabled, submit_btn_label,
        new_state, load_more_style, False, "Load more results"
    )


# ==========================================
#  Pagination for "Load more results" button
# ==========================================

@callback(
    Output("load-more-btn", "disabled"),
    Output("load-more-btn", "children"),
    Output("load-more-trigger-store", "data"),
    Input("load-more-btn", "n_clicks"),
    prevent_initial_call=True,
)
def set_load_more_loading(n_clicks):
    """
    When the user clicks the "Load more results" button, we set it to a loading
    state and trigger the loading of more results.
    """
    if not n_clicks:
        raise PreventUpdate
    return True, "Loading...", n_clicks


@callback(
    Output("explore-results-grid", "children", allow_duplicate=True),
    Output("search-state-store", "data", allow_duplicate=True),
    Output("load-more-btn", "style", allow_duplicate=True),
    Output("load-more-btn", "disabled", allow_duplicate=True),
    Output("load-more-btn", "children", allow_duplicate=True),
    Output("results-summary", "children", allow_duplicate=True),
    State("explore-results-grid", "children"),
    State("search-state-store", "data"),
    Input("load-more-trigger-store", "data"),
    prevent_initial_call=True,
)
def load_more_results(current_images, current_state, trigger_data):
    if not trigger_data or not current_state or not current_state.get("all_ids"):
        raise PreventUpdate

    all_ids = current_state["all_ids"]
    current_offset = current_state.get("offset", 0)
    next_offset = current_offset + 10

    next_batch_ids = all_ids[current_offset:next_offset]

    new_images = [
        html.Div(
            html.Img(
                src=Dataset.get_image_url(artwork_id),
                # Use a dictionary ID for pattern-matching
                id={"type": "thumb-img", "index": artwork_id},
                n_clicks=0,
                style={"cursor": "pointer", "width": "100%"} # Pointer cursor indicates interactivity
            ),
            className="explore-results-item"
        )
        for artwork_id in next_batch_ids
    ]

    updated_grid = (current_images or []) + new_images

    if next_offset >= len(all_ids):
        load_more_style = {"display": "none"}
        btn_disabled = True
    else:
        load_more_style = {"display": "block"}
        btn_disabled = False

    summary = html.P(f"Found {len(all_ids)} images. Displaying top {len(updated_grid)} results.")

    # Update just the offset pointer for the next cycle
    current_state["offset"] = next_offset

    return (
        updated_grid, current_state, load_more_style,
        btn_disabled, "Load more results", summary
    )


# ==========================================
# Image preview modal
# ==========================================

@callback(
    Output("image-preview-modal", "is_open"),
    Output("modal-preview-img", "src"),
    Input({"type": "thumb-img", "index": ALL}, "n_clicks"),
    State("image-preview-modal", "is_open"),
    prevent_initial_call=True
)
def toggle_image_lightbox(thumb_clicks, is_open):
    ctx = dash.callback_context

    if not ctx.triggered:
        raise PreventUpdate

    trigger = ctx.triggered[0]
    trigger_id = ctx.triggered_id

    if isinstance(trigger_id, dict) and trigger_id.get("type") == "thumb-img":
        if trigger.get("value") is None or trigger.get("value") == 0:
            raise PreventUpdate

        artwork_id = trigger_id["index"]
        large_img_url = Dataset.get_image_url(artwork_id)

        return True, large_img_url

    return False, dash.no_update

# ==========================================
# Scroll down after loading more results
# ==========================================

clientside_callback(
    """
    function(grid_children, current_state) {
        if (!current_state || current_state.offset <= 10) {
            return window.dash_clientside.no_update;
        }

        // Use setTimeout to allow React a split second to paint the new image elements into the real DOM
        setTimeout(function() {
            const container = document.querySelector('.explore-results-inner-container > div > div:first-child');
            if (container) {
                container.scrollTo({
                    top: container.scrollHeight,
                    behavior: 'smooth' // Gives a fluid, animated scrolling motion
                });
            }
        }, 60);

        return window.dash_clientside.no_update;
    }
    """,
    Output("scroll-dummy", "children"),          # Target our hidden layout sink
    Input("explore-results-grid", "children"),   # Fires every time new images land
    State("search-state-store", "data"),         # Checks the offset value
    prevent_initial_call=True
)