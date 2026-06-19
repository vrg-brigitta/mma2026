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


# @callback(
#     State('scatterplot', 'figure'),
#     Input("scatterplot", "selectedData"),
# )
# def scatterplot_is_selected(scatterplot_fig, data_selected):
#     print('Scatterplot is selected')

#     data_selected = scatterplot.get_data_selected_on_scatterplot(scatterplot_fig)

#     group_by_count = (data_selected.groupby(['genre'])['genre']
#                           .agg('count')
#                           .to_frame('count_in_selection')
#                           .reset_index())
#     group_by_count['total_count'] = Dataset.class_count().loc[group_by_count['genre']].values
#     # table_rows = group_by_count.sort_values('count_in_selection', ascending=False).to_dict("records")
#     scatterplot.highlight_class_on_scatterplot(scatterplot_fig, None)


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