"""Choropleth map figure builders (simulation output, climate, SPAM area)."""

import numpy as np
import plotly.graph_objects as go

from .config import MAP_VARIABLES, CLIMATE_VARIABLES, MAP_HEIGHT
from .data import cell_meta, summary, spam_ds, _cell_ids_arr, _x_da, _y_da
from .grid import grid_geojson, all_cell_ids, center_lat, center_lon, MAP_ZOOM
from .aggregates import crop_var_range, crop_var_range_all, precomputed_agg
from .queries import get_climate_map_z, mapbox_layers

def build_output_map(ci, season, map_var, agg_override,
                     sel_cell=None, lasso_cells=None, relayout_data=None):
    """
    Build the simulation output choropleth map figure.

    Constructs a five-trace Plotly figure: a grey background tile for all
    cells, a coloured choropleth for the selected variable, a highlight
    overlay for the clicked cell, a highlight overlay for lasso-selected
    cells, and an invisible scatter layer for lasso tool support.

    Parameters
    ----------
    ci : str
        Crop and irrigation combination, e.g. ``'Maize | rainfed'``.
    season : str
        Season year string (e.g. ``'2008'``) or ``'all'`` for multi-year
        aggregation.
    map_var : str
        Map variable key from ``MAP_VARIABLES``,
        e.g. ``'Dry yield (tonne/ha)'``.
    agg_override : str
        Aggregation function to use when ``season='all'``. Either
        ``'mean'`` or ``'sum'``. Falls back to the variable's
        ``default_agg`` if not a valid value.
    sel_cell : int or None, optional
        Cell ID to highlight with a blue overlay. Default is ``None``.
    lasso_cells : list of int or None, optional
        Cell IDs to highlight with an orange overlay from lasso/box
        selection. Default is ``None``.
    relayout_data : dict or None, optional
        Mapbox relayout event data used to preserve zoom and centre
        between updates. Default is ``None``.

    Returns
    -------
    plotly.graph_objects.Figure
        Complete choropleth map figure, or an empty figure if the
        requested aggregation data is not available.
    """
    
    var_info = MAP_VARIABLES[map_var]
    agg_func = agg_override if agg_override in ['mean', 'sum'] else var_info['default_agg']

    if season == 'all':
        subset    = precomputed_agg.get((ci, map_var, agg_func))
        if subset is None:
            return go.Figure()
        subset    = subset.copy()
        agg_label = f"{'Sum' if agg_func == 'sum' else 'Avg'} all years"
        vmin, vmax = crop_var_range_all[ci][f'{map_var}_{agg_func}']
    else:
        subset    = summary[(summary['crop_irr'] == ci) & (summary['season_label'] == season)].copy()
        agg_label = season
        vmin, vmax = crop_var_range[ci][map_var]

    subset['cell_id_str'] = subset['cell_id'].astype(int).astype(str)

    # Static per-cell fields go into customdata (set once); the varying value is
    # read from z via the hovertemplate. This keeps map updates from shipping a
    # ~3 MB rebuilt hover-text array on every variable switch.
    crop_disp = ci.split(' | ')[0].capitalize()
    irr_disp  = ci.split(' | ')[1]
    customdata = np.column_stack([
        subset['cell_id'].astype(int).to_numpy(),
        subset['x'].to_numpy(),
        subset['y'].to_numpy(),
    ])
    hovertemplate = (
        '<b>Cell %{customdata[0]:.0f}</b><br>'
        'Lon: %{customdata[1]:.3f} | Lat: %{customdata[2]:.3f}<br>'
        f'Crop: {crop_disp} ({irr_disp})<br>'
        f'Period: {agg_label}<br>'
        '──────────────────<br>'
        f'{var_info["label"]}: ' + '%{z:.3f}<br>'
        '<i>Click to view time series</i><extra></extra>'
    )

    sel_locations = [str(sel_cell)] if sel_cell is not None else []
    sel_z         = [1] if sel_cell is not None else []

    # Lasso highlight
    lasso_ids = [str(c) for c in (lasso_cells or [])]
    lasso_z   = [1] * len(lasso_ids)

    traces = [
        go.Choroplethmap(
            geojson=grid_geojson, locations=all_cell_ids,
            z=[0] * len(all_cell_ids),
            colorscale=[[0, '#cccccc'], [1, '#cccccc']],
            showscale=False, marker_opacity=0.4,
            marker_line_width=0.5, marker_line_color='white',
            hoverinfo='skip',
        ),
        go.Choroplethmap(
            geojson=grid_geojson, locations=subset['cell_id_str'],
            z=subset[map_var], zmin=vmin, zmax=vmax,
            colorscale=var_info['sum_colorscale'] if agg_func == 'sum' else var_info['colorscale'],
            marker_opacity=0.95, marker_line_width=0.8, marker_line_color='white',
            colorbar=dict(
                title=dict(text=f"{var_info['label']}<br>({agg_label})",
                           font=dict(size=11, family='Arial, system-ui, sans-serif')),
                thickness=14, len=0.38,
                x=0.98, xanchor='right',
                y=0.02, yanchor='bottom',
                bgcolor='rgba(255,255,255,0.88)',
                bordercolor='rgba(0,0,0,0.12)', borderwidth=1,
                tickfont=dict(family='Arial, system-ui, sans-serif', size=10),
            ),
            customdata=customdata,
            hovertemplate=hovertemplate,
        ),
        # Clicked cell highlight
        go.Choroplethmap(
            geojson=grid_geojson, locations=sel_locations, z=sel_z,
            colorscale=[[0, '#1a6faf'], [1, '#1a6faf']],
            showscale=False, marker_opacity=0.45,
            marker_line_width=2.5, marker_line_color='#1a6faf',
            hoverinfo='skip',
        ),
        # Lasso selected cells highlight
        go.Choroplethmap(
            geojson=grid_geojson, locations=lasso_ids, z=lasso_z,
            colorscale=[[0, '#f39c12'], [1, '#f39c12']],
            showscale=False, marker_opacity=0.35,
            marker_line_width=2, marker_line_color='#f39c12',
            hoverinfo='skip',
        ),
        # Invisible centroid scatter for lasso tool
        go.Scattermap(
            lat=[cell_meta[int(cid)]['y'] for cid in all_cell_ids],
            lon=[cell_meta[int(cid)]['x'] for cid in all_cell_ids],
            mode='markers',
            marker=dict(size=8, opacity=0),
            text=all_cell_ids,
            hoverinfo='skip',
            showlegend=False,
        ),
    ]

    if relayout_data and 'map.zoom' in relayout_data:
        map_cfg = dict(
            style='white-bg',
            center=relayout_data.get('map.center', dict(lat=center_lat, lon=center_lon)),
            zoom=relayout_data['map.zoom'],
            layers=mapbox_layers(),
        )
    else:
        map_cfg = dict(
            style='white-bg',
            center=dict(lat=center_lat, lon=center_lon),
            zoom=MAP_ZOOM, layers=mapbox_layers(),
        )

    return go.Figure(
        data=traces,
        layout=go.Layout(
            map=map_cfg,
            margin=dict(l=0, r=0, t=0, b=0),
            height=MAP_HEIGHT, paper_bgcolor='white', uirevision='constant',
            font=dict(family='Arial, system-ui, sans-serif'),
            annotations=[
                dict(x=0.016, y=0.100, xref='paper', yref='paper',
                     text='↑', font=dict(size=26, color='#2c3e50', family='Arial'),
                     showarrow=False, align='center'),
                dict(x=0.016, y=0.048, xref='paper', yref='paper',
                     text='N', font=dict(size=12, color='#2c3e50', family='Arial'),
                     showarrow=False, align='center',
                     bgcolor='rgba(255,255,255,0.82)',
                     bordercolor='rgba(0,0,0,0.10)', borderpad=4, borderwidth=1),
            ],
        )
    )

def build_input_map(climate_var, season_label, sel_cell=None, relayout_data=None):
    """
    Build the climate input choropleth map figure.

    Renders a three-trace figure: a grey background tile, a coloured
    choropleth of the aggregated climate variable, and a highlight overlay
    for the clicked cell. Hover text shows the variable's map label and
    unit (e.g. mm/year for precipitation) while the time series y-axis
    uses the daily label (mm/day).

    Parameters
    ----------
    climate_var : str
        Climate variable key from ``CLIMATE_VARIABLES``,
        e.g. ``'Precipitation'``, ``'MaxTemp'``.
    season_label : str
        Season year string or ``'all'`` for the full period average.
    sel_cell : int or None, optional
        Cell ID to highlight with a blue overlay. Default is ``None``.
    relayout_data : dict or None, optional
        Mapbox relayout event data to preserve zoom and centre. Default
        is ``None``.

    Returns
    -------
    plotly.graph_objects.Figure
        Climate choropleth map figure, or an empty figure if the variable
        is not loaded.
    """

    var_info = CLIMATE_VARIABLES[climate_var]
    z_tuple  = get_climate_map_z(climate_var, season_label)

    if z_tuple is None:
        return go.Figure()

    z_vals    = list(z_tuple)
    locations = [str(int(c)) for c in _cell_ids_arr]
    # The input-map cell set never changes, so locations + customdata are set
    # here once and never re-sent; updates patch only z and the hovertemplate.
    customdata = np.column_stack([
        _cell_ids_arr.astype(int),
        np.array([cell_meta[int(c)]['x'] for c in _cell_ids_arr]),
        np.array([cell_meta[int(c)]['y'] for c in _cell_ids_arr]),
    ])
    hovertemplate = (
        '<b>Cell %{customdata[0]:.0f}</b><br>'
        'Lon: %{customdata[1]:.3f} | Lat: %{customdata[2]:.3f}<br>'
        f'{var_info["map_label"]}: ' + '%{z:.3f}' + f' {var_info["unit"]}<br>'
        '<i>Click to view time series</i><extra></extra>'
    )

    vmin = min(z_vals)
    vmax = max(z_vals)
    period_label = 'All years (daily mean)' if season_label == 'all' else f'{season_label} (daily mean)'

    sel_locations = [str(sel_cell)] if sel_cell is not None else []
    sel_z         = [1] if sel_cell is not None else []

    traces = [
        go.Choroplethmap(
            geojson=grid_geojson, locations=all_cell_ids,
            z=[0] * len(all_cell_ids),
            colorscale=[[0, '#cccccc'], [1, '#cccccc']],
            showscale=False, marker_opacity=0.4,
            marker_line_width=0.5, marker_line_color='white',
            hoverinfo='skip',
        ),
        go.Choroplethmap(
            geojson=grid_geojson, locations=locations,
            z=z_vals, zmin=vmin, zmax=vmax,
            colorscale=var_info['colorscale'],
            marker_opacity=0.95, marker_line_width=0.8, marker_line_color='white',
            colorbar=dict(
                title=dict(text=f"{var_info['unit']}<br>({period_label})", font=dict(size=11)),
                thickness=16, len=0.55, x=1.01,
            ),
            customdata=customdata,
            hovertemplate=hovertemplate,
        ),
        go.Choroplethmap(
            geojson=grid_geojson, locations=sel_locations, z=sel_z,
            colorscale=[[0, '#1a6faf'], [1, '#1a6faf']],
            showscale=False, marker_opacity=0.45,
            marker_line_width=2.5, marker_line_color='#1a6faf',
            hoverinfo='skip',
        ),
    ]

    if relayout_data and 'map.zoom' in relayout_data:
        map_cfg = dict(
            style='white-bg',
            center=relayout_data.get('map.center', dict(lat=center_lat, lon=center_lon)),
            zoom=relayout_data['map.zoom'],
            layers=mapbox_layers(),
        )
    else:
        map_cfg = dict(
            style='white-bg',
            center=dict(lat=center_lat, lon=center_lon),
            zoom=MAP_ZOOM, layers=mapbox_layers(),
        )

    return go.Figure(
        data=traces,
        layout=go.Layout(
            map=map_cfg,
            margin=dict(l=0, r=0, t=0, b=0),
            height=MAP_HEIGHT, paper_bgcolor='white', uirevision='constant',
        )
    )
def build_spam_map(spam_var, sel_cell=None, relayout_data=None):
    """
    Build the SPAM crop physical area choropleth map figure.

    Renders harvested physical area (hectares) for the selected SPAM
    variable. NaN values are replaced with zero. Colour scale is YlGn.

    Parameters
    ----------
    spam_var : str
        SPAM dataset variable name, e.g. ``'Maize_rf_physical_area'``.
    sel_cell : int or None, optional
        Cell ID to highlight with a blue overlay. Default is ``None``.
    relayout_data : dict or None, optional
        Mapbox relayout event data to preserve zoom and centre. Default
        is ``None``.

    Returns
    -------
    plotly.graph_objects.Figure
        SPAM choropleth figure, or an empty figure if the variable is not
        in the SPAM dataset.
    """

    if spam_ds is None or spam_var not in spam_ds.data_vars:
        return go.Figure()

    label       = spam_var.replace('_physical_area', '').replace('_', ' ')
    z_raw       = spam_ds[spam_var].sel(x=_x_da, y=_y_da, method='nearest').values
    z_arr       = np.where(np.isnan(z_raw), 0.0, z_raw)
    z_vals      = z_arr.tolist()
    locations   = [str(int(c)) for c in _cell_ids_arr]
    hover_texts = [
        f"<b>Cell {cid}</b><br>Lon: {cell_meta[cid]['x']:.3f} | Lat: {cell_meta[cid]['y']:.3f}<br>{label}: {val:.2f} ha"
        for cid, val in zip(_cell_ids_arr.tolist(), z_vals)
    ]

    vmin = 0
    vmax = max(z_vals) if max(z_vals) > 0 else 1
    sel_locations = [str(sel_cell)] if sel_cell is not None else []
    sel_z         = [1] if sel_cell is not None else []

    traces = [
        go.Choroplethmap(
            geojson=grid_geojson, locations=all_cell_ids,
            z=[0] * len(all_cell_ids),
            colorscale=[[0, '#cccccc'], [1, '#cccccc']],
            showscale=False, marker_opacity=0.4,
            marker_line_width=0.5, marker_line_color='white',
            hoverinfo='skip',
        ),
        go.Choroplethmap(
            geojson=grid_geojson, locations=locations,
            z=z_vals, zmin=vmin, zmax=vmax,
            colorscale='YlGn',
            marker_opacity=0.95, marker_line_width=0.8, marker_line_color='white',
            colorbar=dict(
                title=dict(text=label + '<br>(ha)',
                           font=dict(size=11, family='Arial, system-ui, sans-serif')),
                thickness=14, len=0.38,
                x=0.98, xanchor='right',
                y=0.02, yanchor='bottom',
                bgcolor='rgba(255,255,255,0.88)',
                bordercolor='rgba(0,0,0,0.12)', borderwidth=1,
                tickfont=dict(family='Arial, system-ui, sans-serif', size=10),
            ),
            text=hover_texts,
            hovertemplate='%{text}<extra></extra>',
        ),
        go.Choroplethmap(
            geojson=grid_geojson, locations=sel_locations, z=sel_z,
            colorscale=[[0, '#1a6faf'], [1, '#1a6faf']],
            showscale=False, marker_opacity=0.45,
            marker_line_width=2.5, marker_line_color='#1a6faf',
            hoverinfo='skip',
        ),
    ]

    if relayout_data and 'map.zoom' in relayout_data:
        map_cfg = dict(
            style='white-bg',
            center=relayout_data.get('map.center', dict(lat=center_lat, lon=center_lon)),
            zoom=relayout_data['map.zoom'],
            layers=mapbox_layers(),
        )
    else:
        map_cfg = dict(
            style='white-bg',
            center=dict(lat=center_lat, lon=center_lon),
            zoom=MAP_ZOOM, layers=mapbox_layers(),
        )

    return go.Figure(
        data=traces,
        layout=go.Layout(
            map=map_cfg,
            margin=dict(l=0, r=0, t=0, b=0),
            height=MAP_HEIGHT, paper_bgcolor='white', uirevision='constant-spam',
            font=dict(family='Arial, system-ui, sans-serif'),
        )
    )
