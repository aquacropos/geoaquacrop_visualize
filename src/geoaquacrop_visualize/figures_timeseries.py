"""Daily time-series figure builders and the shared mean +/- std band."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from .config import DAILY_VARIABLES, CLIMATE_VARIABLES, IRR_MAP, TS_HEIGHT
from .data import (
    cell_meta, crop_irr_list, n_rows, sim_start, year_rows, years,
    preseason_end_row, preseason_end_date,
)
from .utils import hex_to_rgba
from .queries import get_daily, get_climate_series, get_cropcal_values

def _add_mean_std_band(fig, df_plot, var_col, color, year_start, year_end, ts_clicks):
    """
    Add a mean ± std shaded band to a time series figure based on click state.

    Reads a two-click window from ``ts_clicks`` and overlays a filled band
    between mean − std and mean + std, a dashed mean line, two vertical
    boundary lines, and an annotation box showing the computed statistics.
    Adds instructional annotations when fewer than two clicks have been made.

    Parameters
    ----------
    fig : plotly.graph_objects.Figure
        Existing figure to add traces and annotations to.
    df_plot : pandas.DataFrame
        DataFrame with a ``date`` column and a column named ``var_col``
        containing the plotted variable values.
    var_col : str
        Column name of the variable to compute statistics on.
    color : str
        Hex colour string used for the band fill and mean line.
    year_start : pandas.Timestamp
        Start of the visible x-axis range, used to clamp the selection window.
    year_end : pandas.Timestamp
        End of the visible x-axis range.
    ts_clicks : dict or None
        Click state dict with keys ``count`` (int), ``start`` (str or None),
        ``end`` (str or None).

    Returns
    -------
    plotly.graph_objects.Figure
        The input figure with band traces and annotations added in-place.
    """

    if ts_clicks and ts_clicks.get('start') and ts_clicks.get('end'):
        sel_start = max(pd.Timestamp(ts_clicks['start']), year_start)
        sel_end   = min(pd.Timestamp(ts_clicks['end']),   year_end)
        mask      = (df_plot['date'] >= sel_start) & (df_plot['date'] <= sel_end)
        df_sel    = df_plot[mask]

        if not df_sel.empty:
            mean_val = df_sel[var_col].mean()
            std_val  = df_sel[var_col].std()
            upper    = mean_val + std_val
            lower    = mean_val - std_val
            x_band   = list(df_sel['date']) + list(df_sel['date'])[::-1]
            y_band   = ([upper] * len(df_sel)) + ([lower] * len(df_sel))

            fig.add_trace(go.Scatter(
                x=x_band, y=y_band, fill='toself',
                fillcolor=hex_to_rgba(color, 0.20),
                line=dict(width=0), hoverinfo='skip', name='Mean ± Std',
            ))
            fig.add_trace(go.Scatter(
                x=list(df_sel['date']), y=[mean_val] * len(df_sel),
                mode='lines', line=dict(color=color, width=2, dash='dash'),
                hoverinfo='skip', name='Mean',
            ))
            for boundary in [sel_start, sel_end]:
                fig.add_vline(x=boundary.timestamp() * 1000,
                              line=dict(color='#555555', width=1, dash='dot'))
            fig.add_annotation(
                x=sel_start + (sel_end - sel_start) / 2, y=upper,
                text=(f"Mean: {mean_val:.4f}<br>Std: {std_val:.4f}<br>"
                      f"{sel_start.strftime('%b %d')} – {sel_end.strftime('%b %d %Y')}"),
                showarrow=False,
                bgcolor='rgba(255,255,255,0.85)',
                bordercolor=color, borderwidth=1, borderpad=5,
                font=dict(size=11, family='Arial'), yanchor='bottom',
            )
    elif ts_clicks and ts_clicks.get('count') == 1:
        fig.add_annotation(x=0.5, y=1.02, xref='paper', yref='paper',
                           text='Click a second point to set the end of the window',
                           showarrow=False, font=dict(size=13, color='#888888'))
    else:
        fig.add_annotation(x=0.5, y=1.02, xref='paper', yref='paper',
                           text='Click two points to compute mean ± std  |  Third click resets',
                           showarrow=False, font=dict(size=13, color='#888888'))
    return fig

def build_output_ts(cell_id, season_label, daily_var, ts_period, ts_clicks=None):
    """
    Build the daily time series figure for a simulation output variable.

    Renders a line chart with an optional pre-season shading rectangle
    and an interactive mean ± std band computed from user click selections.
    Shows a placeholder prompt when no cell is selected.

    Parameters
    ----------
    cell_id : int or None
        Cell ID to plot. Passing ``None`` returns a placeholder figure.
    season_label : str
        Season year string (e.g. ``'2008'``) or ``'all'``. When ``'all'``,
        ``ts_period`` is forced to ``'full'``.
    daily_var : str
        Daily variable key from ``DAILY_VARIABLES``, e.g. ``'Es'``.
    ts_period : str
        ``'season'`` to show only the selected year, ``'full'`` for the
        entire simulation period.
    ts_clicks : dict or None, optional
        Click state dict with keys ``count``, ``start``, ``end`` used to
        define the mean ± std window. Default is ``None``.

    Returns
    -------
    plotly.graph_objects.Figure
        Line chart figure, or an empty figure if cell data is unavailable.
    """

    var_info = DAILY_VARIABLES[daily_var]

    if ts_period == 'full' or season_label == 'all':
        row_start, row_end = 0, n_rows - 1
        year_start = sim_start
        year_end   = sim_start + pd.to_timedelta(row_end, unit='D')
    else:
        row_start, row_end = year_rows[season_label]
        year_start = sim_start + pd.to_timedelta(row_start, unit='D')
        year_end   = sim_start + pd.to_timedelta(row_end,   unit='D')

    base_layout = dict(
        height=TS_HEIGHT, paper_bgcolor='white', plot_bgcolor='#f9f9f9',
        margin=dict(l=70, r=20, t=60, b=50),
        xaxis=dict(range=[str(year_start.date()), str(year_end.date())],
                   showgrid=True, gridcolor='#eeeeee', title='Date'),
        yaxis=dict(title=var_info['label'], showgrid=True, gridcolor='#eeeeee'),
        showlegend=False,
    )

    if cell_id is None:
        fig = go.Figure()
        fig.update_layout(
            title=dict(text='← Click a cell on the map to view daily time series',
                       font=dict(size=13, color='#888888'), x=0.5),
            **base_layout)
        return fig

    wf, cg = get_daily(cell_id)
    if wf is None:
        return go.Figure()

    df      = wf if var_info['table'] == 'water_flux' else cg
    df_plot = df.iloc[row_start:row_end + 1].copy()
    meta    = cell_meta[cell_id]
    period_label = 'Full simulation' if ts_period == 'full' else season_label

    fig = go.Figure()

    if row_start <= preseason_end_row:
        shade_end = min(preseason_end_date, year_end)
        fig.add_vrect(
            x0=str(year_start.date()), x1=str(shade_end.date()),
            fillcolor='rgba(180,180,180,0.2)', layer='below', line_width=0,
            annotation_text='Pre-season', annotation_position='top left',
            annotation_font=dict(size=11, color='#888888'),
        )

    fig.add_trace(go.Scatter(
        x=df_plot['date'], y=df_plot[daily_var], mode='lines',
        line=dict(color=var_info['color'], width=1.8),
        hovertemplate='%{x|%b %d %Y}<br>' + var_info['label'] + ': %{y:.4f}<extra></extra>',
        name='Daily',
    ))

    fig = _add_mean_std_band(fig, df_plot, daily_var, var_info['color'],
                             year_start, year_end, ts_clicks)

    fig.update_layout(
        title=dict(
            text=(f"Cell {cell_id} | ({meta['x']:.3f}, {meta['y']:.3f}) | "
                  f"{meta['crop'].capitalize()} ({meta['irrigation']}) | {period_label}"),
            font=dict(size=13, family='Arial'), x=0.5),
        **base_layout)
    return fig

def build_input_ts(cell_id, climate_var, season_label, ts_period, ts_clicks=None, sel_crop_irr=None):
    """
    Build the climate input daily time series figure for a single cell.

    Renders a line chart with optional pre-season shading, planting date
    vertical lines (one per year in the simulation), and an interactive
    mean ± std band from user click selections.

    Parameters
    ----------
    cell_id : int or None
        Cell ID to plot. Passing ``None`` returns a placeholder figure.
    climate_var : str
        Climate variable key from ``CLIMATE_VARIABLES``.
    season_label : str
        Season year string or ``'all'`` for the full simulation period.
    ts_period : str
        ``'season'`` or ``'full'``.
    ts_clicks : dict or None, optional
        Click state dict for the mean ± std window. Default is ``None``.
    sel_crop_irr : str or None, optional
        Crop and irrigation string used to look up planting DOY from the
        crop calendar. Falls back to ``crop_irr_list[0]`` if ``None``.

    Returns
    -------
    plotly.graph_objects.Figure
        Climate time series figure, or an empty figure if cell data or
        climate data is unavailable.
    """

    if sel_crop_irr is None:
        sel_crop_irr = crop_irr_list[0]
    var_info = CLIMATE_VARIABLES[climate_var]

    if ts_period == 'full' or season_label == 'all':
        year_start = sim_start
        year_end   = sim_start + pd.to_timedelta(n_rows - 1, unit='D')
    else:
        row_start, row_end = year_rows[season_label]
        year_start = sim_start + pd.to_timedelta(row_start, unit='D')
        year_end   = sim_start + pd.to_timedelta(row_end,   unit='D')

    base_layout = dict(
        height=TS_HEIGHT, paper_bgcolor='white', plot_bgcolor='#f9f9f9',
        margin=dict(l=70, r=20, t=60, b=50),
        xaxis=dict(range=[str(year_start.date()), str(year_end.date())],
                   showgrid=True, gridcolor='#eeeeee', title='Date'),
        yaxis=dict(title=var_info['label'], showgrid=True, gridcolor='#eeeeee'),
        showlegend=False,
    )

    if cell_id is None:
        fig = go.Figure()
        fig.update_layout(
            title=dict(text='← Click a cell on the map to view climate time series',
                       font=dict(size=13, color='#888888'), x=0.5),
            **base_layout)
        return fig

    meta = cell_meta.get(cell_id)
    if meta is None:
        return go.Figure()

    df = get_climate_series(climate_var, meta['x'], meta['y'])
    if df is None:
        return go.Figure()

    mask    = (df['date'] >= year_start) & (df['date'] <= year_end)
    df_plot = df[mask].copy()

    fig = go.Figure()

    if year_start <= preseason_end_date:
        shade_end = min(preseason_end_date, year_end)
        fig.add_vrect(
            x0=str(year_start.date()), x1=str(shade_end.date()),
            fillcolor='rgba(180,180,180,0.2)', layer='below', line_width=0,
            annotation_text='Pre-season', annotation_position='top left',
            annotation_font=dict(size=11, color='#888888'),
        )

    # Use currently selected crop from function parameter
    crop_name_ci = sel_crop_irr.split(' | ')[0].capitalize()
    irr_code_ci  = IRR_MAP.get(sel_crop_irr.split(' | ')[1], sel_crop_irr.split(' | ')[1])
    cal_var      = f'{crop_name_ci}_{irr_code_ci}_planting'
    planting_doy = get_cropcal_values(cal_var, meta['x'], meta['y'])
    if planting_doy is not None and not np.isnan(planting_doy):
        for yr in years:
            try:
                plant_date = pd.Timestamp(f'{yr}-01-01') + pd.to_timedelta(int(planting_doy) - 1, unit='D')
                if year_start <= plant_date <= year_end:
                    fig.add_vline(
                        x=plant_date.timestamp() * 1000,
                        line=dict(color='#27ae60', width=1.5, dash='dash'),
                        annotation_text=f'Planting {yr}',
                        annotation_position='top right',
                        annotation_font=dict(size=10, color='#27ae60'),
                    )
            except Exception:
                pass

    fig.add_trace(go.Scatter(
        x=df_plot['date'], y=df_plot[climate_var], mode='lines',
        line=dict(color=var_info['color'], width=1.8),
        hovertemplate='%{x|%b %d %Y}<br>' + var_info['label'] + ': %{y:.3f}<extra></extra>',
        name=var_info['label'],
    ))

    fig = _add_mean_std_band(fig, df_plot, climate_var, var_info['color'],
                             year_start, year_end, ts_clicks)

    period_label = 'Full simulation' if ts_period == 'full' else season_label
    fig.update_layout(
        title=dict(
            text=(f"Cell {cell_id} | ({meta['x']:.3f}, {meta['y']:.3f}) | "
                  f"{var_info['label']} | {period_label}"),
            font=dict(size=13, family='Arial'), x=0.5),
        **base_layout)
    return fig
