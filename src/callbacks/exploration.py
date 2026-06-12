import threading
from io import BytesIO

import torch
from dash import Input, Output, callback, State
from diffusers import StableDiffusionPipeline
from src import config, utils

lock = threading.Lock()
pipe = StableDiffusionPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5"
).to('cuda' if torch.cuda.is_available() else ('mps' if torch.backends.mps.is_available() else 'cpu'))

@callback(
    Output('explore-button', 'disabled'),
    Output('exploration-prompt', 'disabled'),
    State('exploration-prompt', 'value'),
    Input('explore-button', 'n_clicks'),
    prevent_initial_call=True,
)
def explore_from_prompt(prompt, _):
    print('Explore button is pressed, waiting to acquire lock on model')
    with lock:
        print('Lock on model acquired')
        # TODO: use the prompt to explore the dataset 
        # select the relevant subset of the data and update the other visualizations accordingly


    return False, False

@callback(
    Output('explore-button', 'disabled', allow_duplicate=True),
    Output('exploration-prompt', 'disabled', allow_duplicate=True),
    Input('explore-button', 'n_clicks'),
    prevent_initial_call=True,
)
def explore_from_prompt(_):
    return True, True
