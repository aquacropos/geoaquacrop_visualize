"""Loads every dataset once, at import time.

Importing this module reads the summary and daily pickles, the region
GeoJSON, the climate NetCDFs, the crop calendar, and the SPAM physical
area grids, then derives the shared lookup tables (``cell_meta``,
``date_index``, ``year_rows``, ...). Python caches modules, so the cost
is paid exactly once per process no matter how many modules import it.
"""

import pickle
import os
import json
import glob
import pandas as pd
import numpy as np
import xarray as xr

from .config import (
    SUMMARY_PKL, DAILY_PKL, GEOJSON_PATH, PROCESSED_DIR, EXPORT_DIR,
    MAP_VARIABLES, DAILY_VARIABLES, CLIMATE_VARIABLES,
)

os.makedirs(EXPORT_DIR, exist_ok=True)

with open(GEOJSON_PATH) as f:
    region_geojson = json.load(f)

with open(SUMMARY_PKL, 'rb') as f:
    summary_raw = pickle.load(f)

frames = []
for item in summary_raw:
    if isinstance(item, pd.DataFrame):
        frames.append(item)
    elif isinstance(item, dict):
        frames.append(pd.DataFrame([item]))

summary = pd.concat(frames, ignore_index=True)
summary.columns = summary.columns.str.strip()
summary['harvest_year'] = pd.to_datetime(summary['Harvest Date (YYYY/MM/DD)']).dt.year
summary = summary.dropna(subset=['harvest_year'])
summary['season_label'] = summary['harvest_year'].astype(int).astype(str)
summary['crop_irr']     = summary['crop'] + ' | ' + summary['irrigation']

with open(DAILY_PKL, 'rb') as f:
    daily_raw = pickle.load(f)

cell_meta      = {}
cell_id_to_idx = {}


for i, df in enumerate(summary_raw):
    if not isinstance(df, pd.DataFrame) or df.empty or 'cell_id' not in df.columns:
        continue
    row = df.iloc[0]
    if pd.notna(row.get('error', None)):
        continue
    cid = int(row['cell_id'])
    cell_meta[cid] = {
        'x':          float(row['x']),
        'y':          float(row['y']),
        'crop':       row['crop'],
        'irrigation': row['irrigation'],
        'list_idx':   i,
    }
    cell_id_to_idx[cid] = i


# Precomputed arrays for vectorized xarray lookups (built once, reused everywhere)
_cell_ids_arr = np.array(list(cell_meta.keys()), dtype=int)
_cell_xs_arr  = np.array([cell_meta[c]['x'] for c in _cell_ids_arr])
_cell_ys_arr  = np.array([cell_meta[c]['y'] for c in _cell_ids_arr])
_x_da = xr.DataArray(_cell_xs_arr, dims='pts')
_y_da = xr.DataArray(_cell_ys_arr, dims='pts')

crop_irr_list    = sorted(summary['crop_irr'].dropna().unique())
season_list      = sorted(summary['season_label'].dropna().unique())
map_var_keys     = list(MAP_VARIABLES.keys())
daily_var_keys   = list(DAILY_VARIABLES.keys())
climate_var_keys = list(CLIMATE_VARIABLES.keys())

first_harvest_date = pd.to_datetime(summary_raw[0].iloc[0]['Harvest Date (YYYY/MM/DD)'])
first_harvest_step = int(summary_raw[0].iloc[0]['Harvest Date (Step)'])
sim_start          = first_harvest_date - pd.to_timedelta(first_harvest_step, unit='D')
sim_end            = sim_start + pd.to_timedelta(len(daily_raw[0]['water_flux']) - 1, unit='D')

n_rows     = len(daily_raw[0]['water_flux'])
date_index = pd.date_range(start=sim_start, periods=n_rows, freq='D')
years = [yr for yr in sorted(date_index.year.unique())
         if (date_index.year == yr).sum() > 5]

year_rows = {}
for yr in years:
    indices = np.where(date_index.year == yr)[0]
    year_rows[str(yr)] = (int(indices[0]), int(indices[-1]))

wf0 = daily_raw[0]['water_flux'].reset_index(drop=True)
preseason_end_row  = int(wf0[wf0['season_counter'] == -1.0].index.max())
preseason_end_date = sim_start + pd.to_timedelta(preseason_end_row, unit='D')


sim_year_start = years[0]
sim_year_end   = years[-1]
year_suffix    = f'{sim_year_start}{sim_year_end}'

climate_ds = {}
for var in climate_var_keys:
    path = os.path.join(PROCESSED_DIR, f'{var}{year_suffix}.nc')
    if os.path.exists(path):
        climate_ds[var] = xr.open_dataset(path)
    else:
        # Fallback: glob if exact filename not found
        matches = glob.glob(os.path.join(PROCESSED_DIR, f'{var}*.nc'))
        if matches:
            climate_ds[var] = xr.open_dataset(matches[0])

cropcal_ds = xr.open_dataset(os.path.join(PROCESSED_DIR, 'cropcalendar.nc'),
                             decode_timedelta=True)

# ── SPAM: load and keep only variables with data ───────────────────────────────
spam_files = glob.glob(os.path.join(PROCESSED_DIR, 'spam*_physical_area.nc'))
spam_path  = spam_files[0] if spam_files else None
spam_ds = xr.open_dataset(spam_path) if spam_path and os.path.exists(spam_path) else None

spam_var_keys = []  # all SPAM vars with data
if spam_ds is not None:
    for var in sorted(spam_ds.data_vars):
        if 'spatial_ref' in var:
            continue
        arr   = spam_ds[var].values.flatten().astype(float)
        valid = arr[(~np.isnan(arr)) & (arr > 0)]
        if len(valid) > 0:
            spam_var_keys.append(var)
