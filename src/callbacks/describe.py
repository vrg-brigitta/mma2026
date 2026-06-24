from dash import Input, Output, State, callback, html, clientside_callback, ALL
from dash.exceptions import PreventUpdate
from src import config

from src.llm_handlers.query_handler import query_handler
from src.widgets.scatterplot import get_data_selected_on_scatterplot


@callback(
    Output("describe-btn", "disabled", allow_duplicate=True),
    Output("describe-btn", "children", allow_duplicate=True),
    Output("describe-trigger-store", "data"),
    Input("describe-btn", "n_clicks"),
    prevent_initial_call=True,
)
def set_describe_loading_state(n_clicks):
    """
    Instantly disables the button and updates the label when clicked.
    """
    if not n_clicks:
        raise PreventUpdate
    return True, "Describing...", n_clicks


@callback(
    Output("results-summary", "children", allow_duplicate=True),
    Output("explore-results-grid", "children", allow_duplicate=True),
    Output("load-more-btn", "style", allow_duplicate=True),
    Output("describe-btn", "disabled", allow_duplicate=True),
    Output("describe-btn", "children", allow_duplicate=True),
    Input("describe-trigger-store", "data"),
    State("canvas-selected-indices-store", "data"),
    State("scatterplot", "relayoutData"),
    prevent_initial_call=True,
)
def run_describe(trigger_data, selected_indices, relayout_data):
    if not trigger_data:
        raise PreventUpdate

    grid_children = []
    load_more_style = {"display": "none"}

    btn_disabled = False
    btn_label = "Describe data"

    data_selected = get_data_selected_on_scatterplot(selected_indices, relayout_data)

    if data_selected.empty:
        return (
            html.Div("No data visible in the current viewport.", className="text-warning"),
            grid_children,
            load_more_style,
            btn_disabled,
            btn_label
        )

    total_points = len(data_selected)

    if total_points > config.DESCRIBE_MAX_POINTS:
        data_selected = data_selected.sample(config.DESCRIBE_MAX_POINTS, random_state=42)
        print(f"Viewport exceeds threshold ({total_points}). Sampled down to {config.DESCRIBE_MAX_POINTS} points.")

    columns = [c for c in query_handler.METADATA_FIELDS if c in data_selected.columns]
    metadata_records = data_selected[columns].to_dict("records")

    result = query_handler.describe(metadata_records)

    if result is None:
        return (
            html.Div("Could not generate a description. Please try again.", className="text-danger"),
            grid_children,
            load_more_style,
            btn_disabled,
            btn_label
        )

    # Remove the dot at the end of each suggestion if it exists, to make the suggestions more concise.
    follow_up_suggestions = [s.strip(".") for s in result.get("suggestions", [])]

    return (
        html.Div([
            html.Div([
                html.P(result.get("summary", "")),
                html.Ul([html.Li(t) for t in result.get("trends", [])]),
                html.P("Follow-up suggestions:", className="mb-0"),
                html.Ul(
                    [
                        html.Li(
                            t, 
                            id={"type": "suggestion", "index": i},
                            n_clicks=0,
                        ) 
                        for i, t in enumerate(follow_up_suggestions)
                    ], 
                    className="follow-up-suggestions"
                ),
            ]),
            html.P(f" Described {min(total_points, config.DESCRIBE_MAX_POINTS)} out of {total_points} images. Numbers behind words refer to the amount of results related to that topic.")
        ], className="describe-results-summary"),
        grid_children,
        load_more_style,
        btn_disabled,
        btn_label
    )


# =================================================
# When a follow-up suggestion is clicked, populate
# the question input and trigger the submit button.
# =================================================

clientside_callback(
    """
    function(n_clicks_list, text_list, currentSubmitClicks) {
        // 1. If suggestions haven't been rendered yet, the array will be empty
        if (!n_clicks_list || n_clicks_list.length === 0) {
            return [dash_clientside.no_update, dash_clientside.no_update];
        }

        const triggered = dash_clientside.callback_context.triggered;
        if (!triggered || triggered.length === 0) {
            return [dash_clientside.no_update, dash_clientside.no_update];
        }

        const propId = triggered[0].prop_id;
        
        try {
            // Dash formats dictionary IDs into a valid JSON string inside prop_id
            // e.g., '{"index":0,"type":"suggestion"}.n_clicks'
            const idPart = propId.split('.n_clicks')[0];
            const idObj = JSON.parse(idPart);
            const clickedIndex = idObj.index;

            // Guard against the initial "mount" trigger when components first appear with 0 clicks
            if (n_clicks_list[clickedIndex] > 0) {
                const selectedText = text_list[clickedIndex];
                const nextSubmitClicks = (currentSubmitClicks || 0) + 1;
                
                return [selectedText, nextSubmitClicks];
            }
        } catch (e) {
            console.error("Error parsing pattern-matching trigger ID:", e);
        }

        return [dash_clientside.no_update, dash_clientside.no_update];
    }
    """,
    Output("question-input", "value"),
    Output("submit-question-btn", "n_clicks"),
    Input({"type": "suggestion", "index": ALL}, "n_clicks"),
    State({"type": "suggestion", "index": ALL}, "children"),
    State("submit-question-btn", "n_clicks"),
    prevent_initial_call=True
)