"""Callbacks that rebuild the output and input time-series figures."""

from dash import Input, Output

from .app_shell import app
from .data import season_list
from .figures_timeseries import build_output_ts, build_input_ts

# ── Output time series ────────────────────────────────────────────────────────
@app.callback(
    Output('output-ts',           'figure'),
    Output('output-ts-container', 'style'),
    Input('sel-out-cell',  'data'),
    Input('sel-season',    'data'),
    Input('sel-daily-var', 'data'),
    Input('out-ts-clicks', 'data'),
)


def update_output_ts(cell_id, season_label, daily_var, ts_clicks):
    """
    Rebuild the output time series figure and control its container visibility.

    Derives the time period from ``season_label`` ('all' → full simulation,
    specific year → season only). Hides the container when no cell is selected.
    """

    effective_period = 'full' if season_label == 'all' else 'season'
    effective_season = season_list[0] if season_label == 'all' else season_label
    hidden  = {'visibility': 'hidden', 'height': '0', 'overflow': 'hidden'}
    visible = {'visibility': 'visible', 'height': 'auto', 'overflow': 'visible'}
    if cell_id is None:
        return (build_output_ts(None, effective_season, daily_var, effective_period, ts_clicks), hidden)
    return (build_output_ts(cell_id, effective_season, daily_var, effective_period, ts_clicks), visible)

# ── Input time series ─────────────────────────────────────────────────────────
@app.callback(
    Output('input-ts',           'figure'),
    Output('input-ts-container', 'style'),
    Input('sel-in-cell',  'data'),
    Input('sel-clim-var', 'data'),
    Input('sel-season',   'data'),
    Input('in-ts-clicks', 'data'),
    Input('sel-crop',     'data'),
)


def update_input_ts(cell_id, clim_var, season_label, ts_clicks, sel_crop):
    """
    Rebuild the input climate time series figure and control container visibility.

    Passes ``sel_crop`` to ``build_input_ts`` so planting date lines use the
    currently selected crop's calendar.
    """

    effective_period = 'full' if season_label == 'all' else 'season'
    effective_season = season_list[0] if season_label == 'all' else season_label
    hidden  = {'visibility': 'hidden', 'height': '0', 'overflow': 'hidden'}
    visible = {'visibility': 'visible', 'height': 'auto', 'overflow': 'visible'}
    if cell_id is None:
        return (build_input_ts(None, clim_var, effective_season, effective_period,
                               ts_clicks, sel_crop_irr=sel_crop), hidden)
    return (build_input_ts(cell_id, clim_var, effective_season, effective_period,
                           ts_clicks, sel_crop_irr=sel_crop), visible)
