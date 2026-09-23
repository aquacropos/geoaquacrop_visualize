"""Callbacks for spatial and temporal selection: map cell clicks, lasso/box
selection, the ribbon captions, and the time-series mean +/- std window."""

from dash import Input, Output, State

from .app_shell import app
from .config import CLIMATE_VARIABLES
from .data import cell_meta

# ── Cell click selection ──────────────────────────────────────────────────────
@app.callback(Output('sel-out-cell', 'data'),
              Input('output-map', 'clickData'),
              prevent_initial_call=True)
def set_out_cell(click_data):
    """Extract and store the clicked cell ID from the output map click event."""

    if click_data is None:
        return None
    pt = click_data['points'][0]
    if 'location' in pt:
        return int(pt['location'])
    return None

@app.callback(Output('sel-in-cell', 'data'),
              Input('input-map', 'clickData'),
              prevent_initial_call=True)
def set_in_cell(click_data):
    """Extract and store the clicked cell ID from the input map click event."""

    if click_data is None:
        return None
    pt = click_data['points'][0]
    if 'location' in pt:
        return int(pt['location'])
    return None

# ── Lasso selection ───────────────────────────────────────────────────────────
@app.callback(
    Output('lasso-cells',       'data'),
    Output('export-cell-label', 'children'),
    Input('output-map',         'selectedData'),
    Input('export-whole-area',  'value'),
    prevent_initial_call=True,
)
def handle_lasso(selected_data, whole_area):
    """
    Process lasso or box selection events on the output map.

    Extracts cell IDs from the invisible scatter layer's text attribute.
    Clears the selection when 'Whole area' is checked in the export panel.

    Parameters
    ----------
    selected_data : dict or None
        Plotly selectedData event from the output map.
    whole_area : list
        Export panel checklist value. Contains ``'all'`` when whole area
        is selected.

    Returns
    -------
    lasso_cells : list of int
        Selected cell IDs.
    label : str
        Status label shown next to the export cells checklist.
    """

    if 'all' in (whole_area or []):
        return [], '  |  Whole area selected'
    if selected_data and selected_data.get('points'):
        cell_ids = []
        for pt in selected_data['points']:
            if 'text' in pt:
                try:
                    cell_ids.append(int(pt['text']))
                except Exception:
                    pass
        if cell_ids:
            return cell_ids, f'  |  {len(cell_ids)} cells selected via lasso/box'
    return [], '  |  or use lasso/box on the map to select cells'

# ── Time series ribbon text ───────────────────────────────────────────────────
@app.callback(
    Output('ts-ribbon-text', 'children'),
    Input('sel-out-cell', 'data'),
    Input('sel-crop',     'data'),
    Input('sel-season',   'data'),
)
def update_ts_ribbon_text(cell_id, crop, season):
    """
    Update the ribbon text above the output time series.

    Shows cell ID, coordinates, crop type, and selected season when a cell
    is selected. Shows a prompt to select a cell otherwise.
    """

    if cell_id is None:
        return 'Select a cell on the map to view time series'
    meta = cell_meta.get(cell_id, {})
    period_label = 'Full simulation' if season == 'all' else season
    return (f"Selected: Cell {cell_id}  |  "
            f"Location: ({meta.get('x', 0):.3f}, {meta.get('y', 0):.3f})  |  "
            f"Crop: {crop}  |  Season: {period_label}")

@app.callback(
    Output('input-ribbon-text', 'children'),
    Input('sel-in-cell',  'data'),
    Input('sel-clim-var', 'data'),
    Input('sel-season',   'data'),
)
def update_input_ribbon_text(cell_id, clim_var, season):
    """
    Update the ribbon text above the input time series.

    Shows cell ID, coordinates, climate variable label, and selected season
    when a cell is selected.
    """

    if cell_id is None:
        return 'Select a cell on the map to view time series'
    meta = cell_meta.get(cell_id, {})
    period_label = 'Full simulation' if season == 'all' else season
    var_label = CLIMATE_VARIABLES.get(clim_var, {}).get('label', clim_var)
    return (f"Selected: Cell {cell_id}  |  "
            f"Location: ({meta.get('x', 0):.3f}, {meta.get('y', 0):.3f})  |  "
            f"Variable: {var_label}  |  Season: {period_label}")

# ── TS click handlers ─────────────────────────────────────────────────────────
def _handle_click(click_data, ts_clicks):
    """
    Update the click state for the mean ± std window tool.

    Implements a three-state cycle: first click sets the start date, second
    click sets the end date (auto-sorted so start < end), third click resets
    the state to allow a new selection.

    Parameters
    ----------
    click_data : dict or None
        Plotly clickData event from a time series graph.
    ts_clicks : dict
        Current click state with keys ``count``, ``start``, ``end``.

    Returns
    -------
    dict
        Updated click state dict.
    """

    if click_data is None:
        return ts_clicks
    clicked_date = click_data['points'][0]['x']
    count = ts_clicks['count']
    if count == 0:
        return {'count': 1, 'start': clicked_date, 'end': None}
    elif count == 1:
        start = ts_clicks['start']
        if clicked_date < start:
            start, clicked_date = clicked_date, start
        return {'count': 2, 'start': start, 'end': clicked_date}
    return {'count': 0, 'start': None, 'end': None}

@app.callback(Output('out-ts-clicks', 'data'),
              Input('output-ts', 'clickData'),
              State('out-ts-clicks', 'data'),
              prevent_initial_call=True)
def handle_out_ts_click(click_data, ts_clicks):
    """Handle click events on the output time series graph."""

    return _handle_click(click_data, ts_clicks)

@app.callback(Output('in-ts-clicks', 'data'),
              Input('input-ts', 'clickData'),
              State('in-ts-clicks', 'data'),
              prevent_initial_call=True)
def handle_in_ts_click(click_data, ts_clicks):
    """Handle click events on the input climate time series graph."""

    return _handle_click(click_data, ts_clicks)

@app.callback(
    Output('out-ts-clicks', 'data', allow_duplicate=True),
    Input('sel-out-cell',  'data'),
    Input('sel-season',    'data'),
    Input('sel-daily-var', 'data'),
    prevent_initial_call=True,
)
def reset_out_clicks(_, __, ___):
    """Reset the output time series click state when cell, season, or variable changes."""

    return {'count': 0, 'start': None, 'end': None}

@app.callback(
    Output('in-ts-clicks', 'data', allow_duplicate=True),
    Input('sel-in-cell',  'data'),
    Input('sel-season',   'data'),
    Input('sel-clim-var', 'data'),
    prevent_initial_call=True,
)
def reset_in_clicks(_, __, ___):
    """Reset the input time series click state when cell, season, or variable changes."""

    return {'count': 0, 'start': None, 'end': None}
