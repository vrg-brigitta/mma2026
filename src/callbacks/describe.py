from dash import Input, Output, State, callback, html
from dash.exceptions import PreventUpdate

from src.llm_handlers.query_handler import query_handler
from src.widgets.scatterplot import get_data_selected_on_scatterplot


@callback(
    Output("results-summary", "children", allow_duplicate=True),
    Output("explore-results-grid", "children", allow_duplicate=True),
    Output("load-more-btn", "style", allow_duplicate=True),
    Input("describe-btn", "n_clicks"),
    State("canvas-selected-indices-store", "data"),
    State("scatterplot", "relayoutData"),
    prevent_initial_call=True,
)
def run_describe(n_clicks, selected_indices, relayout_data):
    if not n_clicks:
        raise PreventUpdate

    grid_children = []
    load_more_style = {"display": "none"}

    data_selected = get_data_selected_on_scatterplot(selected_indices, relayout_data)

    if data_selected.empty:
        return (
            html.Div("No data visible in the current viewport.", className="text-warning"),
            grid_children,
            load_more_style
        )

    total_points = len(data_selected)
    max_points = 200

    if total_points > max_points:
        # Sample random <max_points> points to avoid overwhelming the LLM context window
        data_selected = data_selected.sample(max_points, random_state=42)
        print(f"Viewport exceeds threshold ({total_points}). Sampled down to {max_points} points.")

    # Only extract the schema keys required by the text generation processor
    columns = [c for c in query_handler.METADATA_FIELDS if c in data_selected.columns]
    metadata_records = data_selected[columns].to_dict("records")

    result = query_handler.describe(metadata_records)

    if result is None:
        return (
            html.Div("Could not generate a description. Please try again.", className="text-danger"),
            grid_children,
            load_more_style
        )

    return (
        html.Div([
            html.Div([
                html.P(result.get("summary", "")),
                html.Ul([html.Li(t) for t in result.get("trends", [])]),
            ]),
            html.P(f" Described {min(total_points, max_points)} out of {total_points} images.")
        ]),
        grid_children,
        load_more_style
    )
