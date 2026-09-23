"""Gridded export of daily output to NetCDF, GeoTIFF, and CSV."""

import os
import numpy as np
import pandas as pd
import xarray as xr

from .config import EXPORT_DIR, DAILY_VARIABLES
from .data import cell_meta, cell_id_to_idx, date_index
from .grid import half
from .queries import get_daily

def export_data(selected_cells, export_vars, start_date, end_date, formats):
    """
    Export daily gridded simulation output to NetCDF, GeoTIFF, and/or CSV.

    Assembles a 3D array (time × y × x) for each requested variable by
    iterating over selected cells and reading their daily tables. Writes
    output files to ``EXPORT_DIR`` and returns a status message.

    Parameters
    ----------
    selected_cells : list of int
        Cell IDs to include. Pass ``list(cell_meta.keys())`` for the whole area.
    export_vars : list of str
        Variable names matching keys in ``DAILY_VARIABLES``,
        e.g. ``['Es', 'Tr', 'biomass']``.
    start_date : str
        ISO date string for the start of the export period, e.g. ``'2008-01-01'``.
    end_date : str
        ISO date string for the end of the export period, e.g. ``'2010-12-31'``.
    formats : list of str
        Output format codes. Any combination of ``'nc'`` (NetCDF),
        ``'tif'`` (GeoTIFF, requires rasterio), ``'csv'`` (CSV).

    Returns
    -------
    str
        Human-readable status message listing saved filenames and the output
        directory, or an error message if the date range is empty or no
        variables were exported.

    Notes
    -----
    GeoTIFF export requires the ``rasterio`` package. If not installed, a
    warning is appended to the exported file list and GeoTIFF is skipped.
    The coordinate reference system is always EPSG:4326.
    """

    try:
        import rasterio
        from rasterio.transform import from_bounds
        has_rasterio = True
    except ImportError:
        has_rasterio = False

    # Resolve cell list
    cell_ids = list(cell_meta.keys()) if not selected_cells else [int(c) for c in selected_cells]

    # Date range
    start_ts = pd.Timestamp(start_date)
    end_ts   = pd.Timestamp(end_date)
    mask     = (date_index >= start_ts) & (date_index <= end_ts)
    time_idx = np.where(mask)[0]

    if len(time_idx) == 0:
        return 'No data in selected date range.'

    dates_sel = date_index[mask]

    # Grid axes from all cells
    xs = sorted(set(cell_meta[c]['x'] for c in cell_ids if c in cell_meta))
    ys = sorted(set(cell_meta[c]['y'] for c in cell_ids if c in cell_meta), reverse=True)

    exported = []

    for var in export_vars:
        var_info = DAILY_VARIABLES[var]
        # 3D array: time × y × x, filled with NaN
        arr = np.full((len(dates_sel), len(ys), len(xs)), np.nan, dtype=np.float32)

        for cid in cell_ids:
            if cid not in cell_id_to_idx:
                continue
            wf, cg = get_daily(cid)
            if wf is None:
                continue
            df = wf if var_info['table'] == 'water_flux' else cg
            df_sel = df.iloc[time_idx][var].values

            xi = xs.index(cell_meta[cid]['x'])
            yi = ys.index(cell_meta[cid]['y'])
            arr[:, yi, xi] = df_sel

        base_name = f"{var}_{start_ts.strftime('%Y%m%d')}_{end_ts.strftime('%Y%m%d')}"

        # ── NetCDF ────────────────────────────────────────────────────────────
        if 'nc' in formats:
            ds = xr.Dataset(
                {var: (['time', 'y', 'x'], arr)},
                coords={
                    'time': dates_sel,
                    'y':    ys,
                    'x':    xs,
                }
            )
            ds[var].attrs['long_name'] = var_info['label']
            ds[var].attrs['units']     = var_info['label'].split('(')[-1].replace(')', '') \
                                         if '(' in var_info['label'] else ''
            ds.attrs['description'] = f'GeoAquaCrop output: {var}'
            nc_path = os.path.join(EXPORT_DIR, base_name + '.nc')
            ds.to_netcdf(nc_path)
            exported.append(os.path.basename(nc_path))

        # ── GeoTIFF ───────────────────────────────────────────────────────────
        if 'tif' in formats:
            if not has_rasterio:
                exported.append('(rasterio not installed — GeoTIFF skipped)')
            else:
                x_min = min(xs) - half
                x_max = max(xs) + half
                y_min = min(ys) - half
                y_max = max(ys) + half
                transform = from_bounds(x_min, y_min, x_max, y_max, len(xs), len(ys))
                tif_path = os.path.join(EXPORT_DIR, base_name + '.tif')
                with rasterio.open(
                    tif_path, 'w',
                    driver='GTiff',
                    height=len(ys), width=len(xs),
                    count=len(dates_sel),
                    dtype='float32',
                    crs='EPSG:4326',
                    transform=transform,
                    nodata=np.nan,
                ) as dst:
                    for t_idx in range(len(dates_sel)):
                        dst.write(arr[t_idx], t_idx + 1)
                        dst.update_tags(t_idx + 1, date=str(dates_sel[t_idx].date()))
                exported.append(os.path.basename(tif_path))

        # ── CSV ───────────────────────────────────────────────────────────────
        if 'csv' in formats:
            rows = []
            for t_idx, dt in enumerate(dates_sel):
                for cid in cell_ids:
                    if cid not in cell_id_to_idx:
                        continue
                    xi = xs.index(cell_meta[cid]['x'])
                    yi = ys.index(cell_meta[cid]['y'])
                    rows.append({
                        'date':    str(dt.date()),
                        'cell_id': cid,
                        'x':       cell_meta[cid]['x'],
                        'y':       cell_meta[cid]['y'],
                        var:       arr[t_idx, yi, xi],
                    })
            df_csv  = pd.DataFrame(rows)
            csv_path = os.path.join(EXPORT_DIR, base_name + '.csv')
            df_csv.to_csv(csv_path, index=False)
            exported.append(os.path.basename(csv_path))

    if exported:
        return f"Saved {len(exported)} file(s) to {EXPORT_DIR}: {', '.join(exported)}"
    return 'Nothing exported — check selections.'
