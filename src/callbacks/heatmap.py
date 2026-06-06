from dash import callback, Output, Input, html, no_update

from src.Dataset import Dataset
from src.utils import encode_image

def get_id_from_path(path):
    return path.split('/')[-1].split('.')[0]

@callback(
    Output("heatmap-tooltip", "show"),
    Output("heatmap-tooltip", "bbox"),
    Output("heatmap-tooltip", "children"),
    Input("heatmap", "hoverData"), 
)
def display_hover(hover_data):
    print('Heatmap is hovered')
    if hover_data is None:
        return False, no_update, no_update

    pt = hover_data["points"][0]
    bbox = pt["bbox"]
    x = pt["x"]
    y = pt["y"]
    z = pt["z"]

    id = get_id_from_path(y)
    name = Dataset.attr_data[Dataset.attr_data['image_info_id'] == id]['title'].values[0]
    image_path = y

    with open(image_path, 'rb') as f:
        image = f.read()

    content = [
        html.Img(src=encode_image(image), style={"width": "100%"}), 
        html.P(name, style={"font-weight": "bold", "font-size": "14px"}),
    ]
    if z > 0: 
        certainty = '(guessing)' if z == 1 else '(probably)' if z == 2 else '(definitely)'
        content.append(html.P(x + ' ' + certainty, style={"font-style": "italic", "font-size": "14px"}))

    children = [
        html.Div(content, style={'width': '150px', 'white-space': 'normal'})
    ]

    return True, bbox, children

@callback(
    Output("grid", "selectedRows", allow_duplicate=True),
    Input("heatmap", "clickData"),
    prevent_initial_call=True,
)
def heatmap_is_clicked(click_data):
    print('Heatmap is clicked')

    id = get_id_from_path(click_data['points'][0]['y'])
    name = Dataset.attr_data[Dataset.attr_data['image_info_id'] == id]['title'].values[0]

    # TODO: what to filter on?
    return {'function': f'params.data.class_name == "{name}"'}