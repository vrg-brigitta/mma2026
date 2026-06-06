from dash import Input, Output, callback, State

@callback(
    Output("grid", "selectedRows", allow_duplicate=True),
    Input("histogram", "clickData"),
    prevent_initial_call=True,
)
def histogram_is_clicked(histogram_click):
    print('Histogram is clicked')
    genre = histogram_click['points'][0]['x']
    return {'function': f'params.data.genre == "{genre}"'}
