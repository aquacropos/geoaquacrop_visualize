"""Callbacks for the export modal: date dropdowns, variable merging, and the
export run itself."""

from dash import Input, Output, State

from .app_shell import app
from .data import years, cell_meta, sim_start, sim_end
from .utils import safe_date
from .export import export_data

# ── Date dropdowns: disable when whole period checked ─────────────────────────
@app.callback(
    Output('export-start-year',  'disabled'),
    Output('export-start-month', 'disabled'),
    Output('export-start-day',   'disabled'),
    Output('export-end-year',    'disabled'),
    Output('export-end-month',   'disabled'),
    Output('export-end-day',     'disabled'),
    Input('export-whole-period', 'value'),
)
def toggle_date_dropdowns(whole_period):
    """Disable all export date dropdowns when 'Whole simulation' is checked."""

    disabled = 'whole' in (whole_period or [])
    return [disabled] * 6

# ── Merge categorised export checklists → export-vars store ──────────────────
@app.callback(
    Output('export-vars', 'data'),
    Input('export-vars-flux', 'value'),
    Input('export-vars-soil', 'value'),
    Input('export-vars-crop', 'value'),
)
def merge_export_vars(flux, soil, crop):
    """
    Merge variable selections from three export checklists into one store.

    Parameters
    ----------
    flux : list of str
        Selected water flux variable keys.
    soil : list of str
        Selected soil water variable keys.
    crop : list of str
        Selected crop growth variable keys.

    Returns
    -------
    list of str
        Combined list of all selected export variable keys.
    """

    return (flux or []) + (soil or []) + (crop or [])

# ── Export modal toggle ───────────────────────────────────────────────────────
@app.callback(
    Output('export-modal', 'is_open'),
    Input('export-modal-open',  'n_clicks'),
    Input('export-modal-close', 'n_clicks'),
    State('export-modal', 'is_open'),
    prevent_initial_call=True,
)
def toggle_export_modal(open_n, close_n, is_open):
    """Toggle the export modal open or closed based on button clicks."""

    return not is_open


# ── Export ────────────────────────────────────────────────────────────────────
@app.callback(
    Output('export-status', 'children'),
    Input('export-btn',          'n_clicks'),
    State('export-vars',         'data'),
    State('export-whole-period', 'value'),
    State('export-start-year',   'value'),
    State('export-start-month',  'value'),
    State('export-start-day',    'value'),
    State('export-end-year',     'value'),
    State('export-end-month',    'value'),
    State('export-end-day',      'value'),
    State('export-whole-area',   'value'),
    State('lasso-cells',         'data'),
    State('export-format',       'value'),
    prevent_initial_call=True,
)
def run_export(n_clicks, export_vars, whole_period,
               start_year, start_month, start_day,
               end_year,   end_month,   end_day,
               whole_area, lasso_cells, formats):
    """
    Run the data export when the Export button is clicked.

    Validates variable and format selections, resolves the date range and
    cell list, then calls ``export_data``. Returns a status message shown
    next to the Export button.

    Parameters
    ----------
    n_clicks : int
        Number of times the Export button has been clicked.
    export_vars : list of str
        Combined variable keys from all three export checklists.
    whole_period : list
        Contains ``'whole'`` if the whole simulation period is selected.
    start_year, start_month, start_day : int
        Start date components from the dropdowns.
    end_year, end_month, end_day : int
        End date components from the dropdowns.
    whole_area : list
        Contains ``'all'`` if the whole spatial area is selected.
    lasso_cells : list of int
        Cell IDs from a lasso/box selection, used when whole_area is not set.
    formats : list of str
        Selected export format codes from ``['nc', 'tif', 'csv']``.

    Returns
    -------
    str
        Status message displayed in the export panel.
    """

    if not export_vars:
        return 'Select at least one variable.'
    if not formats:
        return 'Select at least one format.'

    if 'whole' in (whole_period or []):
        start_date = sim_start
        end_date   = sim_end
    else:
        try:
            start_date = safe_date(start_year, start_month, start_day)
            end_date   = safe_date(end_year,   end_month,   end_day)
        except Exception as e:
            return f'Invalid date: {e}'
        if start_date > end_date:
            return 'Start date must be before end date.'

    if 'all' in (whole_area or []) or not lasso_cells:
        selected_cells = list(cell_meta.keys())
    else:
        selected_cells = lasso_cells

    status = export_data(selected_cells, export_vars,
                         str(start_date.date()), str(end_date.date()), formats)
    return status

@app.callback(
    Output('export-btn-wrapper', 'style'),
    Input('sel-tab', 'data'),
)
def toggle_export_btn(sel_tab):
    """Show the Export button only on the Simulation Outputs tab."""

    base = {'position': 'absolute', 'bottom': '14px', 'left': '12px', 'right': '12px'}
    if sel_tab == 'output':
        return {**base, 'display': 'block'}
    return {**base, 'display': 'none'}

# ── Export: constrain end date dropdowns based on start date ─────────────────
@app.callback(
    Output('export-end-year',  'options'),
    Output('export-end-year',  'value'),
    Output('export-end-month', 'options'),
    Output('export-end-month', 'value'),
    Output('export-end-day',   'options'),
    Output('export-end-day',   'value'),
    Input('export-start-year',   'value'),
    Input('export-start-month',  'value'),
    Input('export-start-day',    'value'),
    State('export-end-year',     'value'),
    State('export-end-month',    'value'),
    State('export-end-day',      'value'),
)
def constrain_end_date(sy, sm, sd, ey, em, ed):
    """
    Constrain the export end date dropdowns so the end date cannot precede the start.

    Filters year options to >= start year, month options to >= start month
    when in the same year, and day options to >= start day when in the same
    month and year. Also clamps the currently selected end values if they
    fall outside the new valid ranges.

    Parameters
    ----------
    sy, sm, sd : int
        Start year, month, day.
    ey, em, ed : int
        Currently selected end year, month, day.

    Returns
    -------
    tuple
        Six values: updated options and values for the end year, month,
        and day dropdowns in order
        ``(year_opts, new_ey, month_opts, new_em, day_opts, new_ed)``.
    """

    import calendar
    year_opts  = [{'label': str(y), 'value': y} for y in years if y >= sy]
    new_ey     = ey if ey >= sy else sy
    if new_ey == sy:
        month_opts = [{'label': f'{m:02d}', 'value': m} for m in range(sm, 13)]
        new_em     = em if em >= sm else sm
    else:
        month_opts = [{'label': f'{m:02d}', 'value': m} for m in range(1, 13)]
        new_em     = em
    max_day = calendar.monthrange(new_ey, new_em)[1]
    if new_ey == sy and new_em == sm:
        day_opts = [{'label': f'{d:02d}', 'value': d} for d in range(sd, max_day + 1)]
        new_ed   = ed if ed >= sd else sd
    else:
        day_opts = [{'label': f'{d:02d}', 'value': d} for d in range(1, max_day + 1)]
        new_ed   = min(ed, max_day)
    return year_opts, new_ey, month_opts, new_em, day_opts, new_ed
