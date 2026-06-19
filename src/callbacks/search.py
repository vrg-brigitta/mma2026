import dash
from dash import callback, Input, Output, State, html, clientside_callback, ALL
from dash.exceptions import PreventUpdate

from src.llm_handlers.query_handler import query_handler
from src.llm_handlers.clip_handler import clip_handler
from src.Dataset import Dataset
from src import config
from src.widgets.scatterplot import get_data_selected_on_scatterplot


# ==========================================
#  Invoke search on submit
# ==========================================

def remove_ids_outside_viewport(ids, scores, selected_indices, relayout_data):
    """
    Given a list of IDs, filter out those that are not visible in the current
    viewport of the scatterplot.
    """
    if not selected_indices and not relayout_data:
        return ids
    
    data_selected = get_data_selected_on_scatterplot(selected_indices, relayout_data)
    allowed_ids = set(data_selected.index)
    
    filtered_results = [
        (img_id, score) 
        for img_id, score in zip(ids, scores) 
        if img_id in allowed_ids
    ]

    return filtered_results, len(data_selected)

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
    State("canvas-selected-indices-store", "data"),
    State("scatterplot", "relayoutData"),
    prevent_initial_call=True,
)
def run_initial_search(user_query, store_data, selected_indices, relayout_data):
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

    filtered_results, num_selected = remove_ids_outside_viewport(ids, scores, selected_indices, relayout_data)
    top_pairs = filtered_results[:config.MAX_EXPLORE_RESULTS_IMAGES_PER_PAGE]
    top_ids = [img_id for img_id, score in top_pairs]
    # top_scores = [score for img_id, score in top_pairs] 

    images = [
        html.Div(
            html.Img(
                src=Dataset.get_image_url(artwork_id),
                id={"type": "thumb-img", "index": artwork_id},
                n_clicks=0,
            ),
            className="explore-results-item"
        )
        for artwork_id in top_ids
    ]

    has_more = len(ids) > len(images)
    total_results = len(filtered_results)

    if total_results == 0:
        return (
            [],
            html.P("Your question did not match any images."),
            submit_btn_disabled, submit_btn_label, empty_state, hide_btn, True, "Load more results"
        )


    if total_results < config.MAX_EXPLORE_RESULTS_IMAGES_PER_PAGE:
        load_more_style = {"display": "none"}
        summary = html.P(f"Found {total_results} related images out of {num_selected} selected images with {int(max(scores) * 100)}% confidence.")
    else:
        load_more_style = {"display": "block"}
        summary = html.P(f"Found {total_results} related images out of {num_selected} selected images with {int(max(scores) * 100)}% confidence. Displaying top {len(top_ids)} results.")

    new_state = {
        "all_ids": [img_id for img_id, score in filtered_results],
        "all_scores": [score for img_id, score in filtered_results],
        "num_selected": num_selected,
        "offset": config.MAX_EXPLORE_RESULTS_IMAGES_PER_PAGE
    }

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
    all_scores = current_state["all_scores"]
    current_offset = current_state.get("offset", 0)
    next_offset = current_offset + config.MAX_EXPLORE_RESULTS_IMAGES_PER_PAGE

    next_batch_ids = all_ids[current_offset:next_offset]

    new_images = [
        html.Div(
            html.Img(
                src=Dataset.get_image_url(artwork_id),
                id={"type": "thumb-img", "index": artwork_id},
                n_clicks=0,
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

    total_results = len(all_ids)
    num_selected = current_state["num_selected"]
    
    if total_results < config.MAX_EXPLORE_RESULTS_IMAGES_PER_PAGE:
        summary = html.P(f"Found {total_results} related images out of {num_selected} selected images with {int(max(all_scores) * 100)}% confidence.")
    else:
        summary = html.P(f"Found {total_results} related images out of {num_selected} selected images with {int(max(all_scores) * 100)}% confidence. Displaying top {len(updated_grid)} results.")

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