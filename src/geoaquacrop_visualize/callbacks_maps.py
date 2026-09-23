"""Map-updating callbacks.

These patch only the z-values, hover text, and colour scale of the existing
figures via ``dash.Patch``, leaving the GeoJSON geometry in the browser --
the single biggest reason interactions stay fast on large grids.
"""

import numpy as np
from dash import Input, Output, State, ALL, ctx, Patch, html

from .app_shell import app
from .config import MAP_VARIABLES, CLIMATE_VARIABLES
from .data import summary, spam_ds, _x_da, _y_da
from .aggregates import crop_var_range, crop_var_range_all, precomputed_agg
from .queries import get_climate_map_z, get_cropcal_summary, spam_vars_for_crop
from .styles import FONT_STACK, btn_style

# ── Output map: data layer (Patch only z/text/colorscale — GeoJSON stays in browser) ──
@app.callback(
    Output('output-map', 'figure', allow_duplicate=True),
    Input('sel-crop',    'data'),
    Input('sel-season',  'data'),
    Input('sel-map-var', 'data'),
    Input('sel-agg',     'data'),
    prevent_initial_call=True,
)
def patch_output_map_data(sel_crop, sel_season, sel_map_var, sel_agg):
    """
    Patch the output map's data layer without re-sending the GeoJSON.

    Uses ``dash.Patch`` to update only the choropleth z-values, locations,
    colorscale, colorbar title, and hover text. The GeoJSON geometry remains
    in the browser, making updates significantly faster than a full figure
    rebuild.
    """

    var_info = MAP_VARIABLES[sel_map_var]
    agg_func = sel_agg if sel_agg in ['mean', 'sum'] else var_info['default_agg']

    if sel_season == 'all':
        subset = precomputed_agg.get((sel_crop, sel_map_var, agg_func))
        if subset is None:
            patched = Patch()
            patched['data'][1]['locations'] = []
            patched['data'][1]['z']         = []
            return patched
        # read-only; precomputed_agg frames are shared and must not be mutated
        agg_label = f"{'Sum' if agg_func == 'sum' else 'Avg'} all years"
        vmin, vmax = crop_var_range_all[sel_crop][f'{sel_map_var}_{agg_func}']
    else:
        subset    = summary[(summary['crop_irr'] == sel_crop) & (summary['season_label'] == sel_season)]
        agg_label = sel_season
        vmin, vmax = crop_var_range[sel_crop][sel_map_var]

    crop_disp = sel_crop.split(' | ')[0].capitalize()
    irr_disp  = sel_crop.split(' | ')[1]
    hovertemplate = (
        '<b>Cell %{customdata[0]:.0f}</b><br>'
        'Lon: %{customdata[1]:.3f} | Lat: %{customdata[2]:.3f}<br>'
        f'Crop: {crop_disp} ({irr_disp})<br>'
        f'Period: {agg_label}<br>'
        '──────────────────<br>'
        f'{var_info["label"]}: ' + '%{z:.3f}<br>'
        '<i>Click to view time series</i><extra></extra>'
    )

    # Always cheap: z (~150 KB), the ranges, colorscale, and the small template.
    patched = Patch()
    patched['data'][1]['z']                         = subset[sel_map_var].tolist()
    patched['data'][1]['zmin']                      = float(vmin)
    patched['data'][1]['zmax']                      = float(vmax)
    patched['data'][1]['colorscale']                = var_info['sum_colorscale'] if agg_func == 'sum' else var_info['colorscale']
    patched['data'][1]['hovertemplate']             = hovertemplate
    patched['data'][1]['colorbar']['title']['text'] = f"{var_info['label']}<br>({agg_label})"

    # The cell set only changes when the crop or season changes; only then do we
    # re-send locations + customdata. A pure variable/aggregation switch keeps
    # the existing (identically ordered) locations, so z stays aligned.
    if ctx.triggered_id in ('sel-crop', 'sel-season'):
        patched['data'][1]['locations']  = subset['cell_id'].astype(int).astype(str).tolist()
        patched['data'][1]['customdata'] = np.column_stack([
            subset['cell_id'].astype(int).to_numpy(),
            subset['x'].to_numpy(),
            subset['y'].to_numpy(),
        ]).tolist()
    return patched


# ── Output map: highlight layers (click + lasso) ──────────────────────────────
@app.callback(
    Output('output-map',  'figure', allow_duplicate=True),
    Input('sel-out-cell', 'data'),
    Input('lasso-cells',  'data'),
    prevent_initial_call=True,
)
def patch_output_map_highlights(sel_cell, lasso_cells):
    """
    Patch the output map's click and lasso highlight layers.

    Updates trace indices 2 (clicked cell, blue) and 3 (lasso cells, orange)
    via ``dash.Patch`` without modifying the data or background layers.
    """

    sel_locations = [str(sel_cell)] if sel_cell is not None else []
    sel_z         = [1] if sel_cell is not None else []
    lasso_ids     = [str(c) for c in (lasso_cells or [])]
    lasso_z       = [1] * len(lasso_ids)

    patched = Patch()
    patched['data'][2]['locations'] = sel_locations
    patched['data'][2]['z']         = sel_z
    patched['data'][3]['locations'] = lasso_ids
    patched['data'][3]['z']         = lasso_z
    return patched


# ── Crop calendar info text ───────────────────────────────────────────────────
@app.callback(
    Output('cropcal-info-text', 'children'),
    Input('sel-crop', 'data'),
    Input('sel-tab',  'data'),
)
def update_cropcal_info(sel_crop, sel_tab):
    """
    Update the crop calendar info text shown above the input map.

    Displays planting date, season length, and approximate harvest date
    for the selected crop and irrigation type.
    """

    info = get_cropcal_summary(sel_crop)
    if info is None:
        return 'No crop calendar data found for this crop and irrigation type.'
    return (f"Planting: {info['planting']} (DOY {info['planting_doy']})  |  "
            f"Season length: {info['season_length']} days  |  "
            f"Approx. harvest: {info['harvest']}")


# ── SPAM buttons: show only buttons for the selected crop ─────────────────────
@app.callback(
    Output('spam-btn-container', 'children'),
    Output('sel-spam-var',       'data'),
    Output('input-mode',         'data'),
    Input('sel-crop',    'data'),
    Input({'type': 'spamvar-btn', 'index': ALL}, 'n_clicks'),
    Input('climvar-dd',  'value'),
    State('sel-spam-var', 'data'),
    prevent_initial_call=False,
)
def update_spam_buttons(sel_crop, spam_clicks, clim_val, current_spam_var):
    """
    Rebuild the SPAM variable buttons for the selected crop.

    Generates one button per matching SPAM variable. Sets ``input-mode``
    to ``'spam'`` when a SPAM button is clicked, or back to ``'climate'``
    when a climate variable button is clicked.
    """

    triggered = ctx.triggered_id

    relevant     = spam_vars_for_crop(sel_crop)
    default_spam = relevant[0] if relevant else ''

    if triggered and isinstance(triggered, dict) and triggered.get('type') == 'spamvar-btn':
        active_spam = triggered['index']
        mode = 'spam'
    elif triggered == 'climvar-dd':
        active_spam = current_spam_var or default_spam
        mode = 'climate'
    else:
        active_spam = default_spam
        mode = 'climate'

    # if triggered and isinstance(triggered, dict):
    #     if triggered.get('type') == 'spamvar-btn':
    #         active_spam = triggered['index']
    #         mode = 'spam'
    #     elif triggered == 'climvar-dd':
    #         active_spam = current_spam_var or default_spam
    #         mode = 'climate'
    #     else:
    #         active_spam = default_spam
    #         mode = 'climate'
    # else:
    #     active_spam = default_spam
    #     mode = 'climate'

    if not relevant:
        buttons = [html.Span('No SPAM data for this crop.',
                             style={'fontFamily': FONT_STACK, 'fontSize': '12px',
                                    'color': '#888'})]
    else:
        buttons = [
            html.Button(
                v.replace('_physical_area', '').replace('_', ' '),
                id={'type': 'spamvar-btn', 'index': v},
                n_clicks=0,
                style=btn_style(v == active_spam and mode == 'spam', 'green'),
            )
            for v in relevant
        ]

    return buttons, active_spam, mode


# ── Input map: data layer (Patch only z/text/colorscale — GeoJSON stays in browser) ──
@app.callback(
    Output('input-map',   'figure', allow_duplicate=True),
    Input('sel-clim-var', 'data'),
    Input('sel-spam-var', 'data'),
    Input('input-mode',   'data'),
    Input('sel-season',   'data'),
    prevent_initial_call=True,
)


def patch_input_map_data(sel_clim_var, sel_spam_var, input_mode, sel_season):
    """
    Patch the input map's data layer for both climate and SPAM modes.

    In climate mode: updates z-values from the aggregated climate grid,
    with hover text using ``map_label`` and ``unit`` (e.g. mm/year).
    In SPAM mode: updates z-values from the SPAM physical area dataset,
    with hover text in hectares.
    """

    # The input-map cell set is constant, so locations + customdata were set once
    # at build time and are never re-sent here -- updates patch only z, the
    # ranges, colorscale, and the small hovertemplate string.
    if input_mode == 'spam' and sel_spam_var:
        if spam_ds is None or sel_spam_var not in spam_ds.data_vars:
            return Patch()
        label   = sel_spam_var.replace('_physical_area', '').replace('_', ' ')
        z_raw   = spam_ds[sel_spam_var].sel(x=_x_da, y=_y_da, method='nearest').values
        z_vals  = np.where(np.isnan(z_raw), 0.0, z_raw).tolist()
        z_max   = max(z_vals)
        vmin, vmax = 0.0, (float(z_max) if z_max > 0 else 1.0)
        colorscale = 'YlGn'
        cb_title   = f"{label}<br>(ha)"
        hovertemplate = (
            '<b>Cell %{customdata[0]:.0f}</b><br>'
            'Lon: %{customdata[1]:.3f} | Lat: %{customdata[2]:.3f}<br>'
            f'{label}: ' + '%{z:.2f}' + ' ha<extra></extra>'
        )
    else:
        z_tuple = get_climate_map_z(sel_clim_var, sel_season)
        if z_tuple is None:
            return Patch()
        z_vals     = list(z_tuple)
        var_info   = CLIMATE_VARIABLES[sel_clim_var]
        vmin, vmax = float(min(z_vals)), float(max(z_vals))

        if sel_clim_var in ('Precipitation', 'ReferenceET'):
            period_label = 'All years (total mm)' if sel_season == 'all' else f'{sel_season} (total mm)'
        else:
            period_label = 'All years (daily mean)' if sel_season == 'all' else f'{sel_season} (daily mean)'

        colorscale = var_info['colorscale']
        cb_title = f"{var_info['unit']}<br>({period_label})"
        hovertemplate = (
            '<b>Cell %{customdata[0]:.0f}</b><br>'
            'Lon: %{customdata[1]:.3f} | Lat: %{customdata[2]:.3f}<br>'
            f'{var_info["map_label"]}: ' + '%{z:.3f}' + f' {var_info["unit"]}<br>'
            '<i>Click to view time series</i><extra></extra>'
        )

    patched = Patch()
    patched['data'][1]['z']                         = z_vals
    patched['data'][1]['zmin']                      = vmin
    patched['data'][1]['zmax']                      = vmax
    patched['data'][1]['colorscale']                = colorscale
    patched['data'][1]['hovertemplate']             = hovertemplate
    patched['data'][1]['colorbar']['title']['text'] = cb_title
    return patched


# ── Input map: highlight layer (click) ────────────────────────────────────────
@app.callback(
    Output('input-map',  'figure', allow_duplicate=True),
    Input('sel-in-cell', 'data'),
    prevent_initial_call=True,
)
def patch_input_map_highlight(sel_cell):
    """Patch the input map's click highlight layer (trace index 2)."""

    sel_locations = [str(sel_cell)] if sel_cell is not None else []
    sel_z         = [1] if sel_cell is not None else []
    patched = Patch()
    patched['data'][2]['locations'] = sel_locations
    patched['data'][2]['z']         = sel_z
    return patched
