from dash import callback, Output, Input, State, dash, clientside_callback
from PIL import Image
from src import config

from src.Dataset import Dataset
from src.widgets import scatterplot

# @callback(
#     Output('scatterplot', 'figure', allow_duplicate=True),
#     State('scatterplot', 'figure'),
#     Input('scatterplot', 'relayoutData'),
#     prevent_initial_call=True,
# )
# def scatterplot_is_zoomed(scatterplot_fig, zoom_data):
#     if len(zoom_data) == 1 and 'dragmode' in zoom_data:
#         return dash.no_update

#     if not any(key in zoom_data for key in ['xaxis.range[0]', 'xaxis.range[1]', 'yaxis.range[0]', 'yaxis.range[1]']):
#         return dash.no_update

#     print('Scatterplot is zoomed')
#     return scatterplot.add_images_to_scatterplot(scatterplot_fig, zoom_data)

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
