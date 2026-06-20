import os

from PIL import Image
from dash import dcc, html
import plotly.express
from src.Dataset import Dataset
from src import config
import plotly.graph_objects as go
import dash_bootstrap_components as dbc

trace_colors = plotly.express.colors.qualitative.Plotly

def get_columnNamesFromProjection(projection):
    if projection == 't-SNE':
        x_col, y_col = 'tsne_x', 'tsne_y'
    elif projection == 'UMAP':
        x_col, y_col = 'umap_x', 'umap_y'
    else:
        raise Exception('Projection not found')    
 
    return x_col, y_col

def get_source_from_primary_image(df):
    return df["primary_image"].str.extract(r'^([^_]+)')[0]


def highlight_class_on_scatterplot(scatterplot):
    dataset = Dataset.get()
    sources = get_source_from_primary_image(dataset).unique()

    source_colors = dict(zip(sources, trace_colors))
    
    source_series = get_source_from_primary_image(dataset)
    default_colors = source_series.map(source_colors)

    scatterplot_fig_data = scatterplot['data'][0]
    selected_ids = []
    if 'selectedpoints' in scatterplot_fig_data:
        selected_ids = [dataset.index[i] for i in scatterplot_fig_data['selectedpoints']]
    
    colors = [
        config.SCATTERPLOT_SELECTED_COLOR if image_id in selected_ids else default_colors.loc[image_id]
        for image_id in dataset.index
    ]

    scatterplot['data'][0]['marker'] = {'color': colors}


def add_images_to_scatterplot(scatterplot_fig, zoom_data=None):
    if zoom_data is None:
        zoom_data = {}

    xaxis = scatterplot_fig['layout'].setdefault('xaxis', {})
    yaxis = scatterplot_fig['layout'].setdefault('yaxis', {})

    if 'xaxis.range[0]' in zoom_data and 'xaxis.range[1]' in zoom_data:
        min_x = float(zoom_data['xaxis.range[0]'])
        max_x = float(zoom_data['xaxis.range[1]'])
        xaxis['range'] = [min_x, max_x]
        xaxis['autorange'] = False
    else:
        if 'range' not in xaxis:
            return scatterplot_fig
        min_x, max_x = map(float, xaxis['range'])

    if 'yaxis.range[0]' in zoom_data and 'yaxis.range[1]' in zoom_data:
        min_y = float(zoom_data['yaxis.range[0]'])
        max_y = float(zoom_data['yaxis.range[1]'])
        yaxis['range'] = [min_y, max_y]
        yaxis['autorange'] = False
    else:
        if 'range' not in yaxis:
            return scatterplot_fig
        min_y, max_y = map(float, yaxis['range'])

    scatterplot_fig['layout']['images'] = []

    # TODO support for multiple projections
    x_col, y_col = get_columnNamesFromProjection(config.DEFAULT_PROJECTION) 
    dataset = Dataset.get()

    images_in_zoom = []
    for image_id, row in dataset.iterrows():
        x, y = row[x_col], row[y_col]
        if min_x <= x <= max_x and min_y <= y <= max_y:
            images_in_zoom.append((x, y, image_id))
        if len(images_in_zoom) > config.MAX_IMAGES_ON_SCATTERPLOT:
            return scatterplot_fig

    for x, y, image_id in images_in_zoom:
        # image_path = dataset.loc[image_id]['file_path']
        image_path = os.path.join(config.IMAGES_DIR, str(image_id) + '.jpg')
        scatterplot_fig['layout']['images'].append(dict(
            x=x,
            y=y,
            source=Image.open(image_path),
            xref="x",
            yref="y",
            sizex=.05,
            sizey=.05,
            xanchor="center",
            yanchor="middle",
        ))
    return scatterplot_fig

def create_scatterplot_figure(projection):
    x_col, y_col = get_columnNamesFromProjection(projection)

    fig = plotly.express.scatter(data_frame=Dataset.get(), x=x_col, y=y_col,
        labels=dict(zip((x_col, y_col), ('x', 'y'))))

    fig.update_traces(
        customdata=Dataset.get().index, 
        marker={'color': config.SCATTERPLOT_COLOR},
        unselected_marker_opacity=0.6,
        selected_marker_color=config.SCATTERPLOT_SELECTED_COLOR, 
    )
    fig.update_layout(dragmode='select')

    fig.update_xaxes(title=None, showticklabels=False)
    fig.update_yaxes(scaleanchor="x", scaleratio=1, title=None, showticklabels=False)

    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            name='selected',
            marker=dict(size=7, color="red", symbol='circle'),
        ),
    )

    dataset = Dataset.get()
    sources = get_source_from_primary_image(dataset).unique()
    source_colors = dict(zip(sources, trace_colors))

    for source in sources:
        fig.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode="markers",
                name=source,
                marker=dict(size=7, color=source_colors[source], symbol='circle'),
            ),
        )

    source_series = get_source_from_primary_image(dataset)
    colors = source_series.map(source_colors)
    fig.data[0].marker.color = colors

    buttons = [
        dict(
            label="All",
            method="update",
            args=[{"visible": [True] * (len(sources) + 1)}],
        ) 
    ]

    for i, source in enumerate(sources):
        # Create a visibility list where only the current index is True
        visibility = [False] * (len(sources) + 1)
        visibility[i+1] = True

        buttons.append(
            dict(
                label=f"{source} Only",
                method="update",
                args=[{"visible": visibility}],
            )
        )

    fig.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                buttons=buttons,
        )]
    )

    fig.update_layout(legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="left",
        x=0
    ))
    return fig


def create_scatterplot(projection):
    return html.Div([
        dcc.Store(id="canvas-selected-indices-store", data=[]),

        dcc.Graph(
            figure=create_scatterplot_figure(projection),
            id='scatterplot',
            className='stretchy-widget border-widget',
            responsive=True,
            config={
                'displaylogo': False,
                'modeBarButtonsToRemove': ['resetScale2d', 'lasso2d', 'toImage'],
                'displayModeBar': True,
                'showAxisDragHandles': True,
                'showTips': True,
                'scrollZoom': True,
            }
        )
    ], style={'height': '100%', 'width': '100%', 'position': 'relative'})


def get_data_selected_on_scatterplot(selected_indices, relayout_data, projection='UMAP'):
    """
    Optimized helper accepting pre-stripped integer indices from the client store.
    """
    dataset = Dataset.get()
    x_col, y_col = ('umap_x', 'umap_y') if projection == 'UMAP' else ('tsne_x', 'tsne_y')

    if selected_indices:
        return dataset.iloc[selected_indices]

    # Viewport fallback (Zoom/Pan)
    if relayout_data and all(k in relayout_data for k in ['xaxis.range[0]', 'xaxis.range[1]', 'yaxis.range[0]', 'yaxis.range[1]']):
        min_x = float(relayout_data['xaxis.range[0]'])
        max_x = float(relayout_data['xaxis.range[1]'])
        min_y = float(relayout_data['yaxis.range[0]'])
        max_y = float(relayout_data['yaxis.range[1]'])

        visible_mask = (
            (dataset[x_col] >= min_x) & (dataset[x_col] <= max_x) &
            (dataset[y_col] >= min_y) & (dataset[y_col] <= max_y)
        )
        return dataset[visible_mask]

    return dataset
