import time

from dash import Patch, callback, Output, Input, State, dash, clientside_callback
from src import config

from src.widgets import scatterplot

_SCATTERPLOT_ZOOM_DEBOUNCE_LAST_RUN = 0.0
_SCATTERPLOT_ZOOM_DEBOUNCE_SECONDS = 0.5

clientside_callback(
    f"""
    function(relayoutData, figure, thresholdState) {{
        const threshold = {config.SCATTERPLOT_IMAGE_ZOOM_THRESHOLD};
        if (!relayoutData || Object.keys(relayoutData).length === 0) {{
            return window.dash_clientside.no_update;
        }}

        if ('dragmode' in relayoutData && Object.keys(relayoutData).length === 1) {{
            return window.dash_clientside.no_update;
        }}

        if (!figure || !figure.layout || !figure.layout.xaxis || !figure.layout.yaxis) {{
            return window.dash_clientside.no_update;
        }}

        let x0, x1, y0, y1;
        if ('xaxis.range[0]' in relayoutData && 'xaxis.range[1]' in relayoutData &&
            'yaxis.range[0]' in relayoutData && 'yaxis.range[1]' in relayoutData) {{
            x0 = relayoutData['xaxis.range[0]'];
            x1 = relayoutData['xaxis.range[1]'];
            y0 = relayoutData['yaxis.range[0]'];
            y1 = relayoutData['yaxis.range[1]'];
        }} else {{
            const xRange = figure.layout.xaxis.range;
            const yRange = figure.layout.yaxis.range;
            if (!xRange || !yRange || xRange.length !== 2 || yRange.length !== 2) {{
                return window.dash_clientside.no_update;
            }}
            x0 = xRange[0];
            x1 = xRange[1];
            y0 = yRange[0];
            y1 = yRange[1];
        }}

        const span = Math.max(Math.abs(x1 - x0), Math.abs(y1 - y0));
        const active = span <= threshold;
        if (!thresholdState) {{
            thresholdState = {{active: false, relayoutData: null, zoomSpan: null, xaxisRange: null, yaxisRange: null}};
        }}

        const prevActive = thresholdState.active;
        const prevRelayout = thresholdState.relayoutData ? JSON.stringify(thresholdState.relayoutData) : null;
        const currentRelayout = JSON.stringify(relayoutData);

        if (!active && !prevActive) {{
            return window.dash_clientside.no_update;
        }}

        const payload = {{
            active: active,
            relayoutData: relayoutData,
            zoomSpan: span,
            xaxisRange: [x0, x1],
            yaxisRange: [y0, y1],
        }};

        if (active && (!prevActive || currentRelayout !== prevRelayout)) {{
            return payload;
        }}

        if (!active && prevActive) {{
            return payload;
        }}

        return window.dash_clientside.no_update;
    }}
    """,
    Output('scatterplot-zoom-threshold-store', 'data'),
    Input('scatterplot', 'relayoutData'),
    State('scatterplot', 'figure'),
    State('scatterplot-zoom-threshold-store', 'data'),
    prevent_initial_call=True,
)

@callback(
    Output('scatterplot', 'figure', allow_duplicate=True),
    Output('scatterplot-images-store', 'data'),
    Input('scatterplot-zoom-threshold-store', 'data'),
    State('canvas-selected-indices-store', 'data'),
    State('scatterplot-images-store', 'data'),
    prevent_initial_call=True,
)
def scatterplot_is_zoomed(threshold_state, selected_indices, images_store):
    global _SCATTERPLOT_ZOOM_DEBOUNCE_LAST_RUN

    if not threshold_state or 'zoomSpan' not in threshold_state:
        return dash.no_update, dash.no_update

    now = time.time()
    if now - _SCATTERPLOT_ZOOM_DEBOUNCE_LAST_RUN < _SCATTERPLOT_ZOOM_DEBOUNCE_SECONDS:
        return dash.no_update, dash.no_update
    _SCATTERPLOT_ZOOM_DEBOUNCE_LAST_RUN = now

    zoom_data = threshold_state.get('relayoutData', {})
    zoom_span = threshold_state.get('zoomSpan')
    xaxis_range = threshold_state.get('xaxisRange')
    yaxis_range = threshold_state.get('yaxisRange')

    if zoom_span is None or xaxis_range is None or yaxis_range is None:
        return dash.no_update, dash.no_update

    images_layout, images_store = scatterplot.add_images_to_scatterplot(
        zoom_data=zoom_data,
        zoom_span=zoom_span,
        selected_indices=selected_indices,
        images_store=images_store,
        xaxis_range=xaxis_range,
        yaxis_range=yaxis_range,
        projection=config.DEFAULT_PROJECTION,
    )

    patched_fig = Patch()
    patched_fig['layout']['images'] = images_layout
    patched_fig['layout']['xaxis']['range'] = xaxis_range
    patched_fig['layout']['yaxis']['range'] = yaxis_range

    return patched_fig, images_store


clientside_callback(
    """
    function(selectedData) {
        // If nothing is selected or data is cleared, pass an empty array
        if (!selectedData || !selectedData.points || selectedData.points.length === 0) {
            return [];
        }

        //extract ONLY the integer index and drop the rest
        return selectedData.points.map(p => p.pointIndex);
    }
    """,
    Output("canvas-selected-indices-store", "data"),
    Input("scatterplot", "selectedData"),
    prevent_initial_call=True
)

clientside_callback(
    """
    function(selected_sources, figure) {
        if (!figure || !figure.data || figure.data.length === 0) {
            return figure;
        }

        if (!selected_sources) {
            selected_sources = [];
        }

        // customdata is [[id1, source1], [id2, source2], ...]
        const customDataPairs = figure.data[0].customdata || [];
        const opacities = customDataPairs.map(function(pair) {
            const source = pair ? pair[1] : null;
            return selected_sources.indexOf(source) !== -1 ? 1.0 : 0.0;
        });

        const newFigure = Object.assign({}, figure);
        newFigure.data = figure.data.slice();
        const trace = Object.assign({}, newFigure.data[0]);
        trace.marker = Object.assign({}, trace.marker || {}, {opacity: opacities});
        newFigure.data[0] = trace;
        return newFigure;
    }
    """,
    Output("scatterplot", "figure"),
    Input("source-visibility-checklist", "value"),
    State("scatterplot", "figure"),
    prevent_initial_call=True
)


clientside_callback(
    """
    function(searchState, figure) {
        if (!figure || !figure.data || figure.data.length === 0) {
            return [window.dash_clientside.no_update, window.dash_clientside.no_update];
        }

        if (!window._lastProcessedSearchKey) {
            window._lastProcessedSearchKey = null;
        }

        const currentSearchKey = searchState && searchState.all_ids ? JSON.stringify(searchState.all_ids) : null;

        // CRITICAL GUARD: Only execute if this is a brand new, unseen search result payload
        if (!currentSearchKey || currentSearchKey === window._lastProcessedSearchKey) {
            return [window.dash_clientside.no_update, window.dash_clientside.no_update];
        }

        window._lastProcessedSearchKey = currentSearchKey;

        const customData = figure.data[0].customdata || [];
        if (customData.length === 0) {
            return [window.dash_clientside.no_update, window.dash_clientside.no_update];
        }

        const searchIds = new Set(searchState.all_ids.map(String));

        const DEFAULT_GRAY = 'rgba(200, 200, 200, 0.5)';
        const SELECTION_RED = 'rgba(255, 0, 0, 0.5)';
        const SEARCH_GREEN = '#27AE60'; // Muted medium emerald green

        const colors = [];
        for (let i = 0; i < customData.length; i++) {
            const pair = customData[i];
            if (pair && searchIds.has(String(pair[0]))) {
                colors.push(SEARCH_GREEN);
            } else {
                colors.push(DEFAULT_GRAY);
            }
        }

        const newFigure = Object.assign({}, figure);
        newFigure.data = figure.data.slice();
        const trace = Object.assign({}, newFigure.data[0]);

        // Drop the selection overlay
        if ('selectedpoints' in trace) {
            delete trace.selectedpoints;
        }

        trace.marker = Object.assign({}, trace.marker || {});
        trace.marker.color = colors;

        // Maintain selection tool configuration rules intact for any future lasso/box drawing
        trace.selected = Object.assign({}, trace.selected || {});
        trace.selected.marker = Object.assign({}, trace.selected.marker || {});
        trace.selected.marker.color = SELECTION_RED;

        newFigure.data[0] = trace;

        return [newFigure, null];
    }
    """,
    Output("scatterplot", "figure", allow_duplicate=True),
    Output("scatterplot", "selectedData", allow_duplicate=True),
    Input("search-state-store", "data"),
    State("scatterplot", "figure"),
    prevent_initial_call=True
)
