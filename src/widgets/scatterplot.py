import os

from PIL import Image
from dash import dcc, html
import plotly.express
from src.Dataset import Dataset
from src import config
import plotly.graph_objects as go
import dash_bootstrap_components as dbc

trace_colors = plotly.express.colors.qualitative.Plotly

def get_column_names_from_projection(projection):
    if projection == 't-SNE':
        x_col, y_col = 'tsne_x', 'tsne_y'
    elif projection == 'UMAP':
        x_col, y_col = 'umap_x', 'umap_y'
    else:
        raise Exception('Projection not found')    
 
    return x_col, y_col

def get_source_from_primary_image(df):
    return df["primary_image"].str.extract(r'^([^_]+)')[0]


def get_source_colors(dataset):
    sources = get_source_from_primary_image(dataset).unique()
    return dict(zip(sources, trace_colors))


def build_source_marker_properties(dataset, visible_sources=None):
    source_series = get_source_from_primary_image(dataset)
    source_colors = get_source_colors(dataset)

    colors = source_series.map(source_colors).tolist()
    if visible_sources is None:
        visible_sources = source_series.unique().tolist()

    opacities = [1.0 if source in visible_sources else 0.0 for source in source_series]
    return colors, opacities


def apply_source_visibility(scatterplot_fig, visible_sources):
    dataset = Dataset.get()
    colors, opacities = build_source_marker_properties(dataset, visible_sources)

    marker = scatterplot_fig['data'][0].get('marker', {})
    #marker['color'] = colors
    marker['opacity'] = opacities
    scatterplot_fig['data'][0]['marker'] = marker

    return scatterplot_fig


def highlight_class_on_scatterplot(scatterplot, selected_genres=None):
    dataset = Dataset.get()
    source_colors = get_source_colors(dataset)
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

    marker = scatterplot_fig_data.get('marker', {})
    current_opacity = marker.get('opacity', [1.0] * len(dataset))
    marker['color'] = colors
    marker['opacity'] = current_opacity
    scatterplot['data'][0]['marker'] = marker

    return scatterplot


def add_images_to_scatterplot(zoom_data=None, zoom_span=None, selected_indices=None, images_store=None, xaxis_range=None, yaxis_range=None, projection=config.DEFAULT_PROJECTION):
    if zoom_data is None:
        zoom_data = {}

    if images_store is None:
        images_store = []

    if xaxis_range is None or yaxis_range is None:
        return [], []

    if 'xaxis.range[0]' in zoom_data and 'xaxis.range[1]' in zoom_data:
        min_x = float(zoom_data['xaxis.range[0]'])
        max_x = float(zoom_data['xaxis.range[1]'])
    else:
        min_x, max_x = map(float, xaxis_range)

    if 'yaxis.range[0]' in zoom_data and 'yaxis.range[1]' in zoom_data:
        min_y = float(zoom_data['yaxis.range[0]'])
        max_y = float(zoom_data['yaxis.range[1]'])
    else:
        min_y, max_y = map(float, yaxis_range)

    if zoom_span is None:
        span_x = max_x - min_x
        span_y = max_y - min_y
        zoom_span = max(span_x, span_y)

    # If zoomed in enough -> show images of nodes in viewport (or selection); otherwise hide
    if zoom_span <= config.SCATTERPLOT_IMAGE_ZOOM_THRESHOLD:
        visible_df = get_data_selected_on_scatterplot(selected_indices, zoom_data, projection)

        images = []
        count = 0
        for image_id, row in visible_df.iterrows():
            if count >= config.MAX_IMAGES_ON_SCATTERPLOT:
                break
            x, y = row[get_column_names_from_projection(projection)[0]], row[get_column_names_from_projection(projection)[1]]
            image_path = os.path.join(config.IMAGES_DIR, str(image_id) + '.jpg')
            try:
                img_src = Image.open(image_path)
            except Exception:
                continue

            images.append(dict(
                x=x,
                y=y,
                source=img_src,
                xref="x",
                yref="y",
                sizex=.05,
                sizey=.05,
                xanchor="center",
                yanchor="middle",
            ))

            if image_id not in images_store:
                images_store.append(image_id)

            count += 1

        return images, images_store
    else:
        return [], []

def create_scatterplot_figure(projection, dataset, sources_of_dataset, sources):
    x_col, y_col = get_column_names_from_projection(projection)

    source_series = get_source_from_primary_image(dataset)
    marker_colors, marker_opacities = build_source_marker_properties(dataset)

    combined_metadata = list(zip(dataset.index.tolist(), source_series.tolist()))

    fig = go.Figure(
        data=go.Scattergl(
            x=dataset[x_col],
            y=dataset[y_col],
            mode="markers",
            customdata=combined_metadata,
            marker=dict(
                size=7,
                opacity=marker_opacities,
            ),
            selected_marker=dict(color=config.SCATTERPLOT_SELECTED_COLOR),
            unselected_marker=dict(opacity=0.6),
        )
    )

    fig.update_layout(dragmode='select')
    fig.update_xaxes(title=None, showticklabels=False)
    fig.update_yaxes(scaleanchor="x", scaleratio=1, title=None, showticklabels=False)
    fig.update_layout(legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="left",
        x=0
    ))
    return fig


def get_source_label(source: str):
    if source == "MET":
        return 'MET'
    elif source == "UKI":
        return 'Ukiyo-e'
    if source == "GAC":
        return 'Government Art Collection (UK)'
    elif source == "WIKI":
        return 'Wikidata'
    elif source == "SEM":
        return 'SemArt'
    elif source == "RM":
        return 'Rijksmuseum'
    else:
        return source

def create_scatterplot(projection):
    dataset = Dataset.get()
    sources_of_dataset = get_source_from_primary_image(dataset)
    sources = sources_of_dataset.unique()
    return html.Div([
        dcc.Store(id="canvas-selected-indices-store", data=[]),
        dcc.Store(id="scatterplot-images-store", data=[]),
        dcc.Store(id="scatterplot-zoom-threshold-store", data={"active": False, "relayoutData": None}),
        html.Div([
            #dbc.Label("Sources", html_for="source-visibility-checklist", className="form-label"),
            dbc.Checklist(
                id="source-visibility-checklist",
                options=[{"label": get_source_label(source), "value": source} for source in sources],
                value=list(sources),
                inline=True,
                labelClassName="me-3",
            )
        ], className="mb-2 sources-block"),
        dcc.Graph(
            figure=create_scatterplot_figure(projection, dataset, sources_of_dataset, sources),
            id='scatterplot',
            className='stretchy-widget border-widget',
            responsive=True,
            config={
                'displaylogo': False,
                'modeBarButtonsToRemove': ['resetScale2d', 'toImage'],
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
    x_col, y_col = get_column_names_from_projection(projection) 

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
