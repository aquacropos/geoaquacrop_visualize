"""Right canvas column: the output and input map/time-series panels."""

import dash_bootstrap_components as dbc
from dash import dcc, html

from .data import (
    crop_irr_list, season_list, map_var_keys, daily_var_keys, climate_var_keys,
)
from .styles import FONT_STACK, RIBBON_STYLE
from .figures_maps import build_output_map, build_input_map
from .figures_timeseries import build_output_ts, build_input_ts

MAIN_COL = (
dbc.Col(width=9, style={'padding': '0', 'backgroundColor': 'white'}, children=[

    # ── Output panel ──────────────────────────────────────────────────
    html.Div(id='output-panel', children=[

        dcc.Graph(
            id='output-map',
            figure=build_output_map(crop_irr_list[0], season_list[0],
                                    map_var_keys[0], 'mean'),
            config={'scrollZoom': True,
                    'modeBarButtonsToAdd': ['lasso2d', 'select2d']},
            style={'width': '100%'},
        ),

        # Time series ribbon + graph (hidden until a cell is clicked)
        # html.Div(id='output-ts-container', style={'display': 'none'}, children=[
        html.Div(id='output-ts-container', style={'visibility': 'hidden', 'height': '0', 'overflow': 'hidden'}, children=[
            html.Div(style=RIBBON_STYLE, children=[
                html.Span(id='ts-ribbon-text',
                          children='Select a cell on the map to view time series',
                          style={'flexGrow': '1', 'fontFamily': FONT_STACK,
                                 'fontSize': '12px', 'color': '#4a5568'}),
            ]),

            dcc.Graph(
                id='output-ts',
                figure=build_output_ts(None, season_list[0],
                                       daily_var_keys[0], 'season'),
                style={'width': '100%'},
            ),

        ]),

    ]),

    # ── Input panel ───────────────────────────────────────────────────
    html.Div(id='input-panel', style={'display': 'none'}, children=[

        html.Div([
            html.Span('Crop calendar: ', style={
                'fontFamily': FONT_STACK, 'fontSize': '11px',
                'fontWeight': '600', 'color': '#4a5568', 'marginRight': '4px',
            }),
            html.Span(id='cropcal-info-text', children='—',
                      style={'fontFamily': FONT_STACK, 'fontSize': '11px',
                             'color': '#555'}),
        ], style={
            'padding': '5px 14px', 'backgroundColor': '#f8f9fa',
            'borderBottom': '1px solid #dee2e6',
        }),

        dcc.Graph(
            id='input-map',
            figure=build_input_map(climate_var_keys[0], season_list[0]),
            config={'scrollZoom': True},
            style={'width': '100%'},
        ),

        # html.Div(id='input-ts-container', style={'display': 'none'}, children=[
        html.Div(id='input-ts-container', style={'visibility': 'hidden', 'height': '0', 'overflow': 'hidden'}, children=[

            html.Div(style=RIBBON_STYLE, children=[
                html.Span(id='input-ribbon-text',
                          children='Select a cell on the map to view time series',
                          style={'flexGrow': '1', 'fontFamily': FONT_STACK,
                                 'fontSize': '12px', 'color': '#4a5568'}),
            ]),

            dcc.Graph(
                id='input-ts',
                figure=build_input_ts(None, climate_var_keys[0],
                                      season_list[0], 'season'),
                style={'width': '100%'},
            ),

        ]),

    ]),

])  # end canvas col
)
