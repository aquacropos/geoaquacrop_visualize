"""Left sidebar column: tab bar, data configuration, and variable pickers."""

import dash_bootstrap_components as dbc
from dash import dcc, html

from .config import CLIMATE_VARIABLES
from .data import (
    crop_irr_list, season_list, map_var_keys, daily_var_keys, climate_var_keys,
)
from .styles import (
    FONT_STACK, ACCENT, SIDEBAR_BG, SIDEBAR_STYLE, DD_CTRL_STYLE,
    btn_style, _sec_hdr, _ctrl_label, _map_dd_opts, _daily_dd_opts,
    _YIELD_VARS, _WATER_VARS, _WP_VARS, _FLUX_VARS, _SOIL_VARS, _CROP_VARS,
)

SIDEBAR_COL = (
dbc.Col(width=3, style=SIDEBAR_STYLE, children=[

    html.H5('GeoAquaCrop Visualizer', style={
        'fontFamily': FONT_STACK, 'fontWeight': '700',
        'color': "#000000", 'marginBottom': '15px', 'fontSize': '19px',
    }),

    # ── Tab bar ───────────────────────────────────────────────────────
    dcc.Tabs(
        id='main-tabs', value='output',
        style={'marginBottom': '10px'},
        colors={'border': ACCENT, 'primary': ACCENT, 'background': SIDEBAR_BG},
        children=[
            dcc.Tab(
                label='Simulation Outputs', value='output',
                style={'fontFamily': FONT_STACK, 'fontSize': '14px',
                       'padding': '6px 8px', 'color': "#000000", 'fontWeight': '600'},
                selected_style={'fontFamily': FONT_STACK, 'fontSize': '14px',
                                'padding': '6px 8px', 'backgroundColor': ACCENT,
                                'color': 'white', 'borderTop': f'3px solid {ACCENT}'},
            ),
            dcc.Tab(
                label='Inputs', value='input',
                style={'fontFamily': FONT_STACK, 'fontSize': '14px',
                       'padding': '6px 8px', 'color': "#000000",'fontWeight': '600'},
                selected_style={'fontFamily': FONT_STACK, 'fontSize': '14px',
                                'padding': '6px 8px', 'backgroundColor': ACCENT,
                                'color': 'white', 'borderTop': f'3px solid {ACCENT}'},
            ),
        ],
    ),



    # ── Data Configuration ────────────────────────────────────────────
    _sec_hdr('Data Configuration'),
    _ctrl_label('Crop & Irrigation'),
    dcc.Dropdown(
        id='crop-dropdown',
        options=[{'label': ci, 'value': ci} for ci in crop_irr_list],
        value=crop_irr_list[0], clearable=False, style=DD_CTRL_STYLE,
    ),
    _ctrl_label('Season'),
    dcc.Dropdown(
        id='season-dropdown',
        options=(
            [{'label': s, 'value': s} for s in season_list] +
            [{'label': 'All years', 'value': 'all'}]
        ),
        value=season_list[0], clearable=False, style=DD_CTRL_STYLE,
    ),

    # Aggregation (shown only when season=all + output tab)
    html.Div(id='agg-row', style={'display': 'none'}, children=[
        _ctrl_label('Aggregation'),
        html.Div([
            html.Button('Mean', id={'type': 'agg-btn', 'index': 'mean'}, n_clicks=0,
                        style=btn_style(True,  'teal')),
            html.Button('Sum',  id={'type': 'agg-btn', 'index': 'sum'},  n_clicks=0,
                        style=btn_style(False, 'teal')),
        ], style={'marginBottom': '6px'}),
    ]),

    # ── Output controls ───────────────────────────────────────────────
    html.Div(id='output-controls', children=[

        _sec_hdr('Map Variable'),
        dbc.Accordion(flush=True, always_open=True,
                      active_item=['yield'],
                      style={'marginBottom': '10px',
                             'border': '1px solid #e2e8f0',
                             'borderRadius': '6px', 'overflow': 'hidden'},
                      children=[
            dbc.AccordionItem(title='Yield & Production', item_id='yield',
                              style={'padding': '2px 0'}, children=[
                dcc.Dropdown(
                    id='mapvar-yield-dd',
                    options=_map_dd_opts(_YIELD_VARS),
                    value=map_var_keys[0] if map_var_keys[0] in _YIELD_VARS else None,
                    placeholder='Select variable…', clearable=True, 
                    style=DD_CTRL_STYLE,
                ),
            ]),
            dbc.AccordionItem(title='Water Balance', item_id='water',
                              style={'padding': '2px 0'}, children=[
                dcc.Dropdown(
                    id='mapvar-water-dd',
                    options=_map_dd_opts(_WATER_VARS),
                    value=None, placeholder='Select variable…',
                    clearable=True, style=DD_CTRL_STYLE,
                ),
            ]),
            dbc.AccordionItem(title='Water Productivity', item_id='wp',
                              style={'padding': '2px 0'}, children=[
                dcc.Dropdown(
                    id='mapvar-wp-dd',
                    options=_map_dd_opts(_WP_VARS),
                    value=None, placeholder='Select variable…',
                    clearable=True, style=DD_CTRL_STYLE,
                ),
            ]),
        ]),

        _sec_hdr('Daily Variable'), 
        html.Div('Click a cell on the map to view its time series.',
                style={
                    'fontFamily': FONT_STACK, 'fontSize': '11px',
                    'color': '#6c757d', 'fontStyle': 'italic',
                    'marginBottom': '6px',
                }),
        

        dbc.Accordion(flush=True, always_open=True,
                      active_item=['flux'],
                      style={'marginBottom': '10px',
                             'border': '1px solid #e2e8f0',
                             'borderRadius': '6px', 'overflow': 'hidden'},
                      children=[
            dbc.AccordionItem(title='Water Fluxes', item_id='flux',
                              style={'padding': '2px 0'}, children=[
                dcc.Dropdown(
                    id='dailyvar-flux-dd',
                    options=_daily_dd_opts(_FLUX_VARS),
                    value=daily_var_keys[0] if daily_var_keys[0] in _FLUX_VARS else None,
                    placeholder='Select variable…', clearable=True,
                    style=DD_CTRL_STYLE,
                ),
            ]),
            dbc.AccordionItem(title='Soil Water', item_id='soil',
                              style={'padding': '2px 0'}, children=[
                dcc.Dropdown(
                    id='dailyvar-soil-dd',
                    options=_daily_dd_opts(_SOIL_VARS),
                    value=None, placeholder='Select variable…',
                    clearable=True, style=DD_CTRL_STYLE,
                ),
            ]),
            dbc.AccordionItem(title='Crop Development', item_id='crop_dev',
                              style={'padding': '2px 0'}, children=[
                dcc.Dropdown(
                    id='dailyvar-crop-dd',
                    options=_daily_dd_opts(_CROP_VARS),
                    value=None, placeholder='Select variable…',
                    clearable=True, style=DD_CTRL_STYLE,
                ),
            ]),
        ]),

    ]),

    # ── Input controls ────────────────────────────────────────────────
    html.Div(id='input-controls', style={'display': 'none'}, children=[

        _sec_hdr('Climate Variable'),
        html.Div('Click a cell on the map to view its time series.',
                style={
                    'fontFamily': FONT_STACK, 'fontSize': '11px',
                    'color': '#6c757d', 'fontStyle': 'italic',
                    'marginBottom': '6px',
                }),
        dcc.Dropdown(
            id='climvar-dd',
            options=[{'label': CLIMATE_VARIABLES[v]['map_label'], 'value': v}
                     for v in climate_var_keys],
            value=climate_var_keys[0], clearable=False, style=DD_CTRL_STYLE,
        ),

        html.Div(id='spam-btn-row', children=[
            _ctrl_label('Crop Area (SPAM)'),
            html.Span(id='spam-btn-container', children=[]),
        ], style={'marginTop': '8px'}),
    ]),




    # ── Export button pinned at sidebar bottom ────────────────────────
    html.Div(id='export-btn-wrapper', children=[
        html.Button(
            '⬇  Export Data...',
            id='export-modal-open', n_clicks=0,
            style={
                'width': '100%', 'padding': '8px 0',
                'backgroundColor': '#f0f4fa', 'color': ACCENT,
                'border': f'1px solid {ACCENT}', 'borderRadius': '5px',
                'fontFamily': FONT_STACK, 'fontSize': '12px',
                'fontWeight': '600', 'cursor': 'pointer', 'textAlign': 'center',
            },
        ),
    ], style={
        'position': 'absolute', 'bottom': '14px',
        'left': '12px', 'right': '12px',
    }),

])  # end sidebar col
)
