from dash import Input, Output, callback, State

@callback(
    Output("grid", "selectedRows"),
    Input("wordcloud", "click"),
    prevent_initial_call=True,
)
def wordcloud_is_clicked(wordcloud_selection):
    print('Wordcloud is clicked')
    genre = wordcloud_selection[0]
    return {'function': f'params.data.genre == "{genre}"'}
