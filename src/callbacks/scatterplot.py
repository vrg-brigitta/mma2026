from dash import callback, Output, Input, State, dash
from PIL import Image
from src import config

from src.Dataset import Dataset
from src.widgets import scatterplot


@callback(
    Output('scatterplot', 'figure', allow_duplicate=True),
    State('scatterplot', 'figure'),
    Input('scatterplot', 'relayoutData'),
    prevent_initial_call=True,
)
def scatterplot_is_zoomed(scatterplot_fig, zoom_data):
    if len(zoom_data) == 1 and 'dragmode' in zoom_data:
        return dash.no_update

    if not any(key in zoom_data for key in ['xaxis.range[0]', 'xaxis.range[1]', 'yaxis.range[0]', 'yaxis.range[1]']):
        return dash.no_update

    print('Scatterplot is zoomed')
    return scatterplot.add_images_to_scatterplot(scatterplot_fig, zoom_data)


@callback(
    State('scatterplot', 'figure'),
    Input("scatterplot", "selectedData"),
)
def scatterplot_is_selected(scatterplot_fig, data_selected):
    print('Scatterplot is selected')

    scatterplot.highlight_class_on_scatterplot(scatterplot_fig)
