"""Assembles the sidebar, canvas, export modal, and stores into app.layout."""

import dash_bootstrap_components as dbc
from dash import dcc

from .app_shell import app
from .data import (
    crop_irr_list, season_list, map_var_keys, daily_var_keys, climate_var_keys,
)
from .styles import FONT_STACK
from .layout_sidebar import SIDEBAR_COL
from .layout_panels import MAIN_COL
from .layout_export import EXPORT_MODAL

# ══════════════════════════════════════════════════════════════════════════
# STORES
# ══════════════════════════════════════════════════════════════════════════
STORES = [

    dcc.Store(id='sel-tab',        data='output'),
    dcc.Store(id='sel-crop',       data=crop_irr_list[0]),
    dcc.Store(id='sel-season',     data=season_list[0]),
    dcc.Store(id='sel-map-var',    data=map_var_keys[0]),
    dcc.Store(id='sel-daily-var',  data=daily_var_keys[0]),
    dcc.Store(id='sel-clim-var',   data=climate_var_keys[0]),
    dcc.Store(id='sel-agg',        data='mean'),
    dcc.Store(id='sel-out-cell',   data=None),
    dcc.Store(id='sel-in-cell',    data=None),
    dcc.Store(id='out-ts-clicks',  data={'count': 0, 'start': None, 'end': None}),
    dcc.Store(id='in-ts-clicks',   data={'count': 0, 'start': None, 'end': None}),
    dcc.Store(id='lasso-cells',    data=[]),
    dcc.Store(id='sel-spam-var',   data=''),
    dcc.Store(id='input-mode',     data='climate'),
]

app.layout = dbc.Container(fluid=True, style={'fontFamily': FONT_STACK, 'padding': '0'}, children=[

    dbc.Row(className='g-0', children=[
        SIDEBAR_COL,
        MAIN_COL,
    ]),  # end main row

    EXPORT_MODAL,

    *STORES,

])
