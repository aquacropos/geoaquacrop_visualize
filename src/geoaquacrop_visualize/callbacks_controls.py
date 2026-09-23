"""Callbacks for the sidebar controls: tab, crop, season, aggregation, and
the map/daily/climate variable pickers."""

from dash import Input, Output, ALL, ctx

from .app_shell import app
from .data import (
    crop_irr_list, season_list, map_var_keys, daily_var_keys, climate_var_keys,
)
from .styles import btn_style

# ── Tab selection ─────────────────────────────────────────────────────────────
@app.callback(Output('sel-tab', 'data'),
              Input('main-tabs', 'value'))
def set_tab(active_tab):
    """Store the active tab index from tab button clicks."""

    return active_tab or 'output'

@app.callback(
    Output('output-panel',    'style'),
    Output('input-panel',     'style'),
    Output('output-controls', 'style'),
    Output('input-controls',  'style'),
    Input('sel-tab', 'data'),
)
def toggle_tabs(sel_tab):
    """Show or hide the output/input panels and their controls based on active tab."""

    show, hide = {'display': 'block'}, {'display': 'none'}
    if sel_tab == 'output':
        return show, hide, show, hide
    return hide, show, hide, show

# ── Crop & season ─────────────────────────────────────────────────────────────
@app.callback(Output('sel-crop', 'data'),
              Input('crop-dropdown', 'value'))
def set_crop(val):
    """Store the selected crop and irrigation combination."""

    return val or crop_irr_list[0]

@app.callback(Output('sel-season', 'data'),
              Input('season-dropdown', 'value'))
def set_season(val):
    """Store the selected season year or 'all'."""

    return val or season_list[0]

# ── Aggregation ───────────────────────────────────────────────────────────────
@app.callback(Output('sel-agg', 'data'),
              Input({'type': 'agg-btn', 'index': ALL}, 'n_clicks'),
              prevent_initial_call=True)
def set_agg(_):
    """Store the selected aggregation function ('mean' or 'sum')."""

    t = ctx.triggered_id
    return t['index'] if t else 'mean'

@app.callback(
    Output({'type': 'agg-btn', 'index': ALL}, 'style'),
    Input('sel-agg', 'data'),
)
def style_agg_btns(sel_agg):
    """Update aggregation button styles to reflect the active selection."""

    return [btn_style(a == sel_agg, 'teal') for a in ['mean', 'sum']]

@app.callback(
    Output('agg-row', 'style'),
    Input('sel-season', 'data'),
    Input('sel-tab',    'data'),
)
def toggle_agg_row(sel_season, sel_tab):
    """Show the aggregation row only when 'All years' is selected on the output tab."""

    if sel_season == 'all' and sel_tab == 'output':
        return {'display': 'block'}
    return {'display': 'none'}

# ── Map variable selection (three accordion dropdowns → one store) ─────────────
@app.callback(
    Output('sel-map-var',    'data'),
    Output('mapvar-yield-dd', 'value'),
    Output('mapvar-water-dd', 'value'),
    Output('mapvar-wp-dd',    'value'),
    Input('mapvar-yield-dd', 'value'),
    Input('mapvar-water-dd', 'value'),
    Input('mapvar-wp-dd',    'value'),
    prevent_initial_call=True,
)
def set_map_var(yield_v, water_v, wp_v):
    """
    Merge map variable selections from three accordion dropdowns into one store.

    Clears the other two dropdowns when one is selected so only one
    variable is active at a time.
    """

    t = ctx.triggered_id
    if t == 'mapvar-yield-dd' and yield_v:
        return yield_v, yield_v, None, None
    if t == 'mapvar-water-dd' and water_v:
        return water_v, None, water_v, None
    if t == 'mapvar-wp-dd' and wp_v:
        return wp_v, None, None, wp_v
    return map_var_keys[0], map_var_keys[0], None, None

# ── Daily variable selection ──────────────────────────────────────────────────
@app.callback(
    Output('sel-daily-var',    'data'),
    Output('dailyvar-flux-dd', 'value'),
    Output('dailyvar-soil-dd', 'value'),
    Output('dailyvar-crop-dd', 'value'),
    Input('dailyvar-flux-dd', 'value'),
    Input('dailyvar-soil-dd', 'value'),
    Input('dailyvar-crop-dd', 'value'),
    prevent_initial_call=True,
)
def set_daily_var(flux_v, soil_v, crop_v):
    """
    Merge daily variable selections from three accordion dropdowns into one store.

    Clears the other two dropdowns when one is selected.
    """

    t = ctx.triggered_id
    if t == 'dailyvar-flux-dd' and flux_v:
        return flux_v, flux_v, None, None
    if t == 'dailyvar-soil-dd' and soil_v:
        return soil_v, None, soil_v, None
    if t == 'dailyvar-crop-dd' and crop_v:
        return crop_v, None, None, crop_v
    return daily_var_keys[0], daily_var_keys[0], None, None

# ── Climate variable selection ────────────────────────────────────────────────
@app.callback(Output('sel-clim-var', 'data'),
              Input('climvar-dd', 'value'))
def set_clim_var(val):
    """Store the selected climate variable and switch input mode to 'climate'."""

    return val or climate_var_keys[0]
