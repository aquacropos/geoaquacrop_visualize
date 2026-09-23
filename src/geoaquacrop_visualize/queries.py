"""Read-only accessors over the loaded datasets."""

from functools import lru_cache

import numpy as np
import pandas as pd

from .boundary import BOUNDARY_URL
from .config import IRR_MAP
from .data import (
    daily_raw, cell_id_to_idx, sim_start,
    climate_ds, cropcal_ds, spam_var_keys, _x_da, _y_da,
)

@lru_cache(maxsize=None)
def spam_vars_for_crop(crop_irr):
    """
    Find SPAM physical area variable names matching a crop and irrigation type.

    Performs an exact capitalize match first, then falls back to a
    case-insensitive scan of all available SPAM variable keys. Returns an
    empty list when no matching data exists for the crop and irrigation
    combination (e.g. rainfed data not available for an irrigated crop).

    Parameters
    ----------
    crop_irr : str
        Crop and irrigation string in the format ``'CropName | irrigation'``,
        e.g. ``'Maize | rainfed'`` or ``'PaddyRice1 | irrigated'``.

    Returns
    -------
    list of str
        List containing the matching SPAM variable name, or an empty list
        if no match is found. Currently returns at most one element.

    Examples
    --------
    >>> spam_vars_for_crop('Maize | rainfed')
    ['Maize_rf_physical_area']

    >>> spam_vars_for_crop('Wheat | irrigated')
    []
    """
        
    crop_raw = crop_irr.split(' | ')[0]
    irr_code = IRR_MAP.get(crop_irr.split(' | ')[1].strip(),
                           crop_irr.split(' | ')[1].strip())

    # Try exact capitalize match first
    exact = f'{crop_raw.capitalize()}_{irr_code}_physical_area'
    if exact in spam_var_keys:
        return [exact]

    # Fallback: case-insensitive scan of spam_var_keys
    prefix = f'{crop_raw.lower()}_{irr_code}_physical_area'
    for v in spam_var_keys:
        if v.lower() == prefix:
            return [v]

    return []

# ── Crop calendar helper ───────────────────────────────────────────────────────

def get_cropcal_summary(crop_irr):
    """
    Extract crop calendar information for a given crop and irrigation type.

    Reads planting DOY and growing season length from the preprocessed
    ``cropcalendar.nc`` dataset and computes an approximate harvest date.
    Returns ``None`` silently on any error or missing data, so callers
    do not need to handle exceptions.

    Parameters
    ----------
    crop_irr : str
        Crop and irrigation string in the format ``'CropName | irrigation'``,
        e.g. ``'Maize | rainfed'``.

    Returns
    -------
    dict or None
        Dictionary with keys:

        - ``'planting'`` (*str*) — formatted planting date, e.g. ``'May 22'``
        - ``'planting_doy'`` (*int*) — day of year of planting
        - ``'season_length'`` (*int* or *None*) — growing season length in days
        - ``'harvest'`` (*str*) — approximate harvest date, e.g. ``'Oct 06'``

        Returns ``None`` if the crop is not found in the crop calendar dataset
        or if all DOY values are NaN or zero.
    """

    return _get_cropcal_summary_cached(crop_irr)


@lru_cache(maxsize=None)
def _get_cropcal_summary_cached(crop_irr):
    try:
        parts     = crop_irr.split(' | ')
        crop_name = parts[0].capitalize()
        irr_code  = IRR_MAP.get(parts[1], parts[1])
        plant_var = f'{crop_name}_{irr_code}_planting'
        gsl_var   = f'{crop_name}_{irr_code}_growing_season_length'

        if plant_var not in cropcal_ds.data_vars:
            return None

        doy_arr = cropcal_ds[plant_var].values.flatten().astype(float)
        valid   = doy_arr[(~np.isnan(doy_arr)) & (doy_arr > 0)]
        if len(valid) == 0:
            return None
        doy = int(valid[0])
        plant_str = (pd.Timestamp('2001-01-01') +
                     pd.to_timedelta(doy - 1, unit='D')).strftime('%b %d')

        gsl = None
        if gsl_var in cropcal_ds.data_vars:
            raw       = cropcal_ds[gsl_var].values.astype('timedelta64[ns]').astype(float) / 1e9 / 86400
            valid_gsl = raw[(~np.isnan(raw)) & (raw > 0) & (raw < 10000)]
            if len(valid_gsl) > 0:
                gsl = int(valid_gsl[0])

        harvest_str = 'N/A'
        if gsl:
            h_doy = doy + gsl - 1
            harvest_str = (pd.Timestamp('2001-01-01') +
                           pd.to_timedelta(h_doy - 1, unit='D')).strftime('%b %d')

        return {'planting': plant_str, 'planting_doy': doy,
                'season_length': gsl, 'harvest': harvest_str}
    except Exception:
        return None

def get_daily(cell_id):
    """
    Retrieve daily water flux and crop growth tables for a single cell.

    Looks up the cell in ``cell_id_to_idx``, retrieves the corresponding
    entry from ``daily_raw``, and attaches a ``date`` column derived from
    ``sim_start`` and the row index.

    Parameters
    ----------
    cell_id : int
        Integer cell identifier as used in ``cell_meta``.

    Returns
    -------
    wf : pandas.DataFrame or None
        Daily water flux table with a ``date`` column added. Contains columns
        Es, EsPot, Tr, TrPot, Infl, Runoff, DeepPerc, Wr, season_counter.
        Returns ``None`` if the cell is not found or its data is missing.
    cg : pandas.DataFrame or None
        Daily crop growth table with a ``date`` column added. Contains columns
        biomass, canopy_cover, gdd_cum, z_root, DryYield.
        Returns ``None`` alongside ``wf`` when data is unavailable.
    """

    idx = cell_id_to_idx.get(cell_id)
    if idx is None or daily_raw[idx] is None:
        return None, None
    wf = daily_raw[idx]['water_flux'].copy().reset_index(drop=True)
    cg = daily_raw[idx]['crop_growth'].copy().reset_index(drop=True)
    wf['date'] = sim_start + pd.to_timedelta(wf.index, unit='D')
    cg['date'] = sim_start + pd.to_timedelta(cg.index, unit='D')
    return wf, cg
def get_climate_series(var, x, y):
    """
    Extract a daily climate time series at the nearest grid point to (x, y).

    Parameters
    ----------
    var : str
        Climate variable name matching a key in ``CLIMATE_VARIABLES``,
        e.g. ``'Precipitation'``, ``'MaxTemp'``.
    x : float
        Longitude of the target location in decimal degrees.
    y : float
        Latitude of the target location in decimal degrees.

    Returns
    -------
    pandas.DataFrame or None
        Two-column DataFrame with columns ``['date', var]``.
        Returns ``None`` if the variable is not loaded in ``climate_ds``.
    """

    if var not in climate_ds:
        return None
    ds = climate_ds[var]
    pt = ds[var].sel(x=x, y=y, method='nearest')
    df = pt.to_dataframe().reset_index()[['time', var]]
    df.columns = ['date', var]
    return df
def get_climate_map_values(var, season_label):
    """
    Compute spatially aggregated climate values for choropleth map display.

    Averages (or sums for precipitation and reference ET) the climate variable over the
    selected time period. Uses xarray's vectorised selection for efficiency.

    Parameters
    ----------
    var : str
        Climate variable name matching a key in ``CLIMATE_VARIABLES``.
    season_label : str
        Either ``'all'`` for the full simulation period, or a four-digit
        year string (e.g. ``'2008'``) for a single year.

    Returns
    -------
    xarray.DataArray or None
        2D spatial array of aggregated values with dimensions ``(y, x)``.
        Returns ``None`` if the variable is not loaded in ``climate_ds``.
    """
    _SUM_VARS = ('Precipitation', 'ReferenceET')
    if var not in climate_ds:
        return None
    ds = climate_ds[var]
    if season_label == 'all':
        return ds[var].sum(dim='time') if var in _SUM_VARS else ds[var].mean(dim='time')
    yr = int(season_label)
    sel = ds[var].sel(time=ds.time.dt.year == yr)
    return sel.sum(dim='time') if var in _SUM_VARS else sel.mean(dim='time')


@lru_cache(maxsize=None)
def get_climate_map_z(var, season_label):
    """
    Per-cell aggregated climate values ready for a choropleth ``z`` array.

    Wraps :func:`get_climate_map_values` and the nearest-neighbour selection
    onto the cell centroids, then caches the result keyed by
    ``(var, season_label)``. The first call forces the xarray reduction into
    memory; every later call for the same key is a dictionary lookup.


    Returns
    -------
    tuple of float or None
        Per-cell values in ``_cell_ids_arr`` order, or ``None`` if the
        variable is not loaded.
    """
    arr = get_climate_map_values(var, season_label)
    if arr is None:
        return None
    return tuple(arr.sel(x=_x_da, y=_y_da, method='nearest').values.tolist())


def get_cropcal_values(var_name, x, y):
    """
    Extract a single scalar value from the crop calendar dataset at (x, y).

    Parameters
    ----------
    var_name : str
        Variable name in ``cropcal_ds``, e.g. ``'Maize_rf_planting'``.
    x : float
        Longitude in decimal degrees.
    y : float
        Latitude in decimal degrees.

    Returns
    -------
    float or None
        Nearest-neighbour interpolated value, or ``None`` if the variable
        is not present in ``cropcal_ds``.
    """

    if var_name not in cropcal_ds:
        return None
    return float(cropcal_ds[var_name].sel(x=x, y=y, method='nearest').values)

# Built once at import. The region boundary is referenced by URL from the route
# ``boundary`` registers, which serves a thinned copy of ``GEOJSON_PATH``, rather
# than being inlined into every figure: the browser fetches and caches it once
# instead of parsing high MB of geometry per map on every full build. Plotly
# copies whatever it is handed into the figure on construction, so a
# module-level dict would still be serialised -- only the URL keeps the geometry
# out of the figure payload entirely.
MAPBOX_LAYERS = [
    dict(sourcetype='raster',
         source=['https://server.arcgisonline.com/ArcGIS/rest/services/'
                 'World_Topo_Map/MapServer/tile/{z}/{y}/{x}'],
         below='traces'),
    dict(sourcetype='geojson',
         source=BOUNDARY_URL,
         type='line', color='#1a6faf', line=dict(width=2.5)),
]


def mapbox_layers():
    """
    Return the shared Mapbox layer stack used by all map figures.

    A raster tile layer (ESRI World Topo Map) plus a GeoJSON line layer tracing
    the region boundary, the latter loaded by URL from the route
    :func:`~geoaquacrop_visualize.boundary.serve_region_boundary` so the geometry
    is fetched once and browser-cached instead of embedded in each figure.

    Returns
    -------
    list of dict
        Map layer specification dicts compatible with
        ``go.Layout(map=dict(layers=...))`` (MapLibre).
    """

    return MAPBOX_LAYERS
