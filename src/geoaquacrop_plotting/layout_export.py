"""The export modal: variable checklists, date range, extent, and formats."""

import dash_bootstrap_components as dbc
from dash import dcc, html

from .config import DAILY_VARIABLES
from .data import years
from .styles import (
    FONT_STACK, btn_style, dd_style,
    _FLUX_VARS, _SOIL_VARS, _CROP_VARS,
)

EXPORT_MODAL = (
dbc.Modal(id='export-modal', size='lg', is_open=False, children=[

    dbc.ModalHeader(dbc.ModalTitle('Export Gridded Output',
                    style={'fontFamily': FONT_STACK, 'fontSize': '16px'})),

    dbc.ModalBody(style={'fontFamily': FONT_STACK}, children=[

        html.Div([
            html.Label('Variables', style={'fontFamily': FONT_STACK, 'fontWeight': '600',
                                           'fontSize': '12px', 'marginBottom': '8px',
                                           'display': 'block'}),
            # Water Fluxes group
            html.Div([
                html.Div('Water Fluxes', style={
                    'fontFamily': FONT_STACK, 'fontSize': '10px', 'fontWeight': '700',
                    'color': '#7a8a9a', 'letterSpacing': '1px',
                    'textTransform': 'uppercase', 'marginBottom': '4px',
                }),
                dcc.Checklist(
                    id='export-vars-flux',
                    options=[{'label': f'  {DAILY_VARIABLES[v]["label"]}', 'value': v}
                             for v in _FLUX_VARS],
                    value=[_FLUX_VARS[0]], inline=True,
                    style={'fontFamily': FONT_STACK, 'fontSize': '12px'},
                    inputStyle={'marginRight': '4px', 'marginLeft': '12px'},
                ),
            ], style={'marginBottom': '10px', 'paddingBottom': '8px',
                      'borderBottom': '1px solid #e2e8f0'}),
            # Soil Water group
            html.Div([
                html.Div('Soil Water', style={
                    'fontFamily': FONT_STACK, 'fontSize': '10px', 'fontWeight': '700',
                    'color': '#7a8a9a', 'letterSpacing': '1px',
                    'textTransform': 'uppercase', 'marginBottom': '4px',
                }),
                dcc.Checklist(
                    id='export-vars-soil',
                    options=[{'label': f'  {DAILY_VARIABLES[v]["label"]}', 'value': v}
                             for v in _SOIL_VARS],
                    value=[], inline=True,
                    style={'fontFamily': FONT_STACK, 'fontSize': '12px'},
                    inputStyle={'marginRight': '4px', 'marginLeft': '12px'},
                ),
            ], style={'marginBottom': '10px', 'paddingBottom': '8px',
                      'borderBottom': '1px solid #e2e8f0'}),
            # Crop Development group
            html.Div([
                html.Div('Crop Development', style={
                    'fontFamily': FONT_STACK, 'fontSize': '10px', 'fontWeight': '700',
                    'color': '#7a8a9a', 'letterSpacing': '1px',
                    'textTransform': 'uppercase', 'marginBottom': '4px',
                }),
                dcc.Checklist(
                    id='export-vars-crop',
                    options=[{'label': f'  {DAILY_VARIABLES[v]["label"]}', 'value': v}
                             for v in _CROP_VARS],
                    value=[], inline=True,
                    style={'fontFamily': FONT_STACK, 'fontSize': '12px'},
                    inputStyle={'marginRight': '4px', 'marginLeft': '12px'},
                ),
            ]),
            # Hidden merged store consumed by run_export
            dcc.Store(id='export-vars', data=[_FLUX_VARS[0]]),
        ], style={'marginBottom': '14px'}),

        html.Div([
            html.Label('Period', style={'fontFamily': FONT_STACK, 'fontWeight': '600',
                                        'fontSize': '12px', 'marginBottom': '4px',
                                        'display': 'block'}),
            dcc.Checklist(
                id='export-whole-period',
                options=[{'label': '  Whole simulation', 'value': 'whole'}],
                value=[], inline=True,
                style={'display': 'inline', 'fontFamily': FONT_STACK, 'fontSize': '12px'},
                inputStyle={'marginRight': '4px', 'marginLeft': '4px'},
            ),
            html.Span('  From:', style={'fontFamily': FONT_STACK, 'fontSize': '12px',
                                        'marginLeft': '16px'}),
            dcc.Dropdown(id='export-start-year',
                         options=[{'label': str(y), 'value': y} for y in years],
                         value=years[0], clearable=False, style=dd_style('80px')),
            dcc.Dropdown(id='export-start-month',
                         options=[{'label': f'{m:02d}', 'value': m} for m in range(1, 13)],
                         value=1, clearable=False, style=dd_style('70px')),
            dcc.Dropdown(id='export-start-day',
                         options=[{'label': f'{d:02d}', 'value': d} for d in range(1, 32)],
                         value=1, clearable=False, style=dd_style('70px')),
            html.Span('  To:', style={'fontFamily': FONT_STACK, 'fontSize': '12px',
                                      'marginLeft': '12px'}),
            dcc.Dropdown(id='export-end-year',
                         options=[{'label': str(y), 'value': y} for y in years],
                         value=years[-1], clearable=False, style=dd_style('80px')),
            dcc.Dropdown(id='export-end-month',
                         options=[{'label': f'{m:02d}', 'value': m} for m in range(1, 13)],
                         value=12, clearable=False, style=dd_style('70px')),
            dcc.Dropdown(id='export-end-day',
                         options=[{'label': f'{d:02d}', 'value': d} for d in range(1, 32)],
                         value=31, clearable=False, style=dd_style('70px')),
        ], style={'marginBottom': '14px'}),

        html.Div([
            html.Label('Cells', style={'fontFamily': FONT_STACK, 'fontWeight': '600',
                                       'fontSize': '12px', 'marginBottom': '4px',
                                       'display': 'block'}),
            dcc.Checklist(
                id='export-whole-area',
                options=[{'label': '  Whole area', 'value': 'all'}],
                value=['all'], inline=True,
                style={'display': 'inline', 'fontFamily': FONT_STACK, 'fontSize': '12px'},
                inputStyle={'marginRight': '4px', 'marginLeft': '4px'},
            ),
            html.Span(id='export-cell-label',
                      children='  |  or use lasso/box on the map to select cells',
                      style={'fontFamily': FONT_STACK, 'fontSize': '12px',
                             'color': '#888888', 'marginLeft': '8px'}),
        ], style={'marginBottom': '14px'}),

        html.Div([
            html.Label('Format', style={'fontFamily': FONT_STACK, 'fontWeight': '600',
                                        'fontSize': '12px', 'marginBottom': '4px',
                                        'display': 'block'}),
            dcc.Checklist(
                id='export-format',
                options=[
                    {'label': '  NetCDF (.nc)',   'value': 'nc'},
                    {'label': '  GeoTIFF (.tif)', 'value': 'tif'},
                    {'label': '  CSV (.csv)',      'value': 'csv'},
                ],
                value=['csv'], inline=True,
                style={'fontFamily': FONT_STACK, 'fontSize': '12px'},
                inputStyle={'marginRight': '4px', 'marginLeft': '14px'},
            ),
        ]),

    ]),

    dbc.ModalFooter([
        html.Span(id='export-status', children='',
                  style={'fontFamily': FONT_STACK, 'fontSize': '12px',
                         'color': '#27ae60', 'marginRight': 'auto'}),
        html.Button('Export', id='export-btn', n_clicks=0,
                    style={**btn_style(True, 'blue'),
                           'fontSize': '13px', 'padding': '7px 28px'}),
        dbc.Button('Close', id='export-modal-close', n_clicks=0,
                   color='secondary', size='sm',
                   style={'marginLeft': '8px', 'fontFamily': FONT_STACK}),
    ]),

])
)
