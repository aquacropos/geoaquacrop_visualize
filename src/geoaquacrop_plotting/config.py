"""User configuration: file paths, canvas sizes, and variable catalogues.

Edit the values in this module to point the app at a different simulation
run or to change the map/time-series canvas dimensions.
"""

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                        USER CONFIGURATION                                  ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

import os

# ── Where the data lives ──────────────────────────────────────────────────────
# The simulation and preprocessing outputs sit in sibling checkouts:
#
#     <workspace>/geoaquacrop-preproc/
#     <workspace>/geoaquacrop-simulate/
#     <workspace>/Geoaquacrop-visualizer/   ← this project
#
# _WORKSPACE is found by walking up from this file, and then from the working
# directory, until a folder containing geoaquacrop-preproc turns up. That keeps
# working from a source checkout, from an editable install, and from a plain
# `pip install .` where the package is copied into site-packages.
#
# To point the app somewhere else, either set the GEOAQUACROP_ROOT environment
# variable to the folder holding those two trees, or replace the four paths
# below with absolute ones.

_MARKER = 'geoaquacrop-preproc'


def _ascend(start):
    """Yield ``start`` and each of its parent directories, up to the filesystem root."""

    path = os.path.abspath(start)
    while True:
        yield path
        parent = os.path.dirname(path)
        if parent == path:
            return
        path = parent


def _find_workspace():
    """Locate the directory that holds the geoaquacrop-preproc/-simulate trees."""

    override = os.environ.get('GEOAQUACROP_ROOT')
    if override:
        return os.path.abspath(os.path.expanduser(override))
    here = os.path.dirname(os.path.abspath(__file__))
    for start in (here, os.getcwd()):
        for path in _ascend(start):
            if os.path.isdir(os.path.join(path, _MARKER)):
                return path
    # Nothing found — fall back to the sibling-of-project-root layout so the
    # error message below reports the conventional location.
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


_WORKSPACE = _find_workspace()

# Exports are written next to the project when run from a checkout, and into the
# working directory when the package is installed into site-packages.
_PKG_PARENT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_INSTALLED  = os.path.basename(_PKG_PARENT) in ('site-packages', 'dist-packages')
_BASE       = os.getcwd() if _INSTALLED else _PKG_PARENT

#: Seasonal per-cell results, as a pickled list of DataFrames. The filename
#: carries the timestamp of the simulation run, so edit it to switch runs.
SUMMARY_PKL   = os.path.join(_WORKSPACE, 'geoaquacrop-simulate/outputs/summary_results_20260521_191549.pkl')

#: Daily per-cell results, as a pickled list of dicts, each holding a
#: ``water_flux`` and a ``crop_growth`` table. Must come from the same run as
#: :data:`SUMMARY_PKL`.
DAILY_PKL     = os.path.join(_WORKSPACE, 'geoaquacrop-simulate/outputs/daily_results_20260521_191549.pkl')

#: The region outline, at full resolution. Read once into
#: ``data.region_geojson`` and thinned in memory by ``boundary``; no copy of it
#: is bundled with the package.
GEOJSON_PATH  = os.path.join(_WORKSPACE, 'geoaquacrop-preproc/inputdata/high_plains.geojson')

#: Directory holding the preprocessed climate, crop-calendar, and SPAM grids.
PROCESSED_DIR = os.path.join(_WORKSPACE, 'geoaquacrop-preproc/processed')

#: Where exports are written. Resolved separately from the input paths and
#: unaffected by ``GEOAQUACROP_ROOT``: it sits beside the package, except when
#: the package is installed into ``site-packages``, in which case the working
#: directory is used so exports never land inside an installed environment.
EXPORT_DIR    = os.path.join(_BASE, 'outputs/exports')

if not os.path.isdir(os.path.join(_WORKSPACE, _MARKER)):
    raise FileNotFoundError(
        f'Could not find the GeoAquaCrop data trees.\n'
        f'  Looked for: {os.path.join(_WORKSPACE, _MARKER)}\n'
        f'  Searched upward from {os.path.dirname(os.path.abspath(__file__))} '
        f'and from {os.getcwd()}\n'
        f'Set GEOAQUACROP_ROOT to the folder containing geoaquacrop-preproc and '
        f'geoaquacrop-simulate, or edit the paths in {os.path.abspath(__file__)}.'
    )


#: Grid cell resolution in decimal degrees. Must match the preprocessing grid:
#: ``grid`` draws each cell as a square of this size centred on the cell
#: coordinates, so a mismatch produces overlapping or gapped polygons.
CELL_RES      = 0.05

#: TCP port the Dash server listens on.
PORT          = 8050

#: Height in pixels of the two choropleth map panels. Also the default canvas
#: height used by :func:`~geoaquacrop_plotting.utils.get_auto_zoom`.
MAP_HEIGHT    = 550

#: Height in pixels of the two time-series panels.
TS_HEIGHT     = 400

# ── Region boundary overlay ───────────────────────────────────────────────────
# GEOJSON_PATH is the only source of the outline. At high MB it is far too heavy
# to hand to Plotly, so boundary.py thins it in memory at startup and serves the
# result from BOUNDARY_URL; nothing is written to disk. Raise the tolerance for
# a coarser, lighter outline, lower it for a crisper, heavier one.
#: Ramer-Douglas-Peucker tolerance in decimal degrees (~400 m at these
#: latitudes, invisible at basin zoom) applied to the outline at startup.
#: Raise it for a coarser, lighter outline; lower it for a crisper, heavier one.
BOUNDARY_SIMPLIFY_EPS = 0.004

#: Path the thinned outline is served from on the Dash server. ``boundary``
#: registers the route here and
#: :func:`~geoaquacrop_plotting.queries.mapbox_layers` points the map layer at
#: it, so the two stay in step through this one constant.
BOUNDARY_URL          = '/region-boundary.geojson'

#: Catalogue of the simulation-output variables the choropleth map can draw.
#: Each key is a column in the summary pickle; each value carries ``label``,
#: ``colorscale`` (used for mean aggregation), ``sum_colorscale``, and
#: ``default_agg``. Adding an entry here also requires listing the key in one
#: of the group constants in ``styles.py`` for it to reach a sidebar accordion.
MAP_VARIABLES = {
    # ── Yield ──────────────────────────────────────────────────────────────────
    'Dry yield (tonne/ha)':                    {'label': 'Dry Yield (t/ha)',              'colorscale': 'YlOrRd',  'sum_colorscale': 'OrRd',   'default_agg': 'mean'},
    'Fresh yield (tonne/ha)':                  {'label': 'Fresh Yield (t/ha)',            'colorscale': 'YlOrRd',  'sum_colorscale': 'OrRd',   'default_agg': 'mean'},
    'Yield potential (tonne/ha)':              {'label': 'Yield Potential (t/ha)',        'colorscale': 'YlOrRd',  'sum_colorscale': 'OrRd',   'default_agg': 'mean'},
    # ── Production & area ──────────────────────────────────────────────────────
    'production_tonnes':                       {'label': 'Production (tonnes)',           'colorscale': 'YlOrBr',  'sum_colorscale': 'OrRd',   'default_agg': 'sum' },
    # ── Water ──────────────────────────────────────────────────────────────────
    'Seasonal irrigation (mm)':                {'label': 'Seasonal Irrigation (mm)',      'colorscale': 'Blues',   'sum_colorscale': 'PuBuGn', 'default_agg': 'sum' },
    'seasonal_precip_mm':                      {'label': 'Seasonal Precip (mm)',          'colorscale': 'Blues',   'sum_colorscale': 'PuBuGn', 'default_agg': 'mean'},
    'seasonal_et_mm':                          {'label': 'Seasonal ET (mm)',              'colorscale': 'YlGnBu',  'sum_colorscale': 'PuBuGn', 'default_agg': 'mean'},
    'seasonal_transpiration_mm':               {'label': 'Seasonal Transpiration (mm)',   'colorscale': 'YlGnBu',  'sum_colorscale': 'PuBuGn', 'default_agg': 'mean'},
    'total_water_input_mm':                    {'label': 'Total Water Input (mm)',        'colorscale': 'Blues',   'sum_colorscale': 'PuBuGn', 'default_agg': 'mean'},
    # ── Water productivity ─────────────────────────────────────────────────────
    'wp_et_kg_per_m3':                         {'label': 'WP-ET (kg/m³)',                 'colorscale': 'RdYlGn',  'sum_colorscale': 'YlGn',   'default_agg': 'mean'},
    'rainfall_use_efficiency_kg_per_m3':       {'label': 'Rainfall Use Efficiency (kg/m³)','colorscale': 'RdYlGn', 'sum_colorscale': 'YlGn',   'default_agg': 'mean'},
   }

#: Catalogue of the daily variables the time-series panel and the export dialog
#: offer. Each key is a column in one of the daily tables; each value carries
#: ``label``, ``table`` (``'water_flux'`` or ``'crop_growth'``), and ``color``.
#: On export the parenthesised tail of ``label`` becomes the NetCDF ``units``.
DAILY_VARIABLES = {
    'Es':           {'label': 'Soil Evaporation (mm/day)',           'table': 'water_flux',  'color': '#e67e22'},
    'EsPot':        {'label': 'Potential Soil Evaporation (mm/day)', 'table': 'water_flux',  'color': '#f39c12'},
    'Tr':           {'label': 'Crop Transpiration (mm/day)',         'table': 'water_flux',  'color': '#2980b9'},
    'TrPot':        {'label': 'Potential Transpiration (mm/day)',    'table': 'water_flux',  'color': '#3498db'},
    'Infl':         {'label': 'Infiltration (mm/day)',               'table': 'water_flux',  'color': '#1abc9c'},
    'Runoff':       {'label': 'Runoff (mm/day)',                     'table': 'water_flux',  'color': '#e74c3c'},
    'DeepPerc':     {'label': 'Deep Percolation (mm/day)',           'table': 'water_flux',  'color': '#8e44ad'},
    'Wr':           {'label': 'Water in Root Zone (mm)',             'table': 'water_flux',  'color': '#2c3e50'},
    'biomass':      {'label': 'Biomass (tonne/ha)',                  'table': 'crop_growth', 'color': '#27ae60'},
    'canopy_cover': {'label': 'Canopy Cover (-)',                    'table': 'crop_growth', 'color': '#2ecc71'},
    'gdd_cum':      {'label': 'Cumulative GDD (°C·day)',            'table': 'crop_growth', 'color': '#d35400'},
    'z_root':       {'label': 'Root Depth (m)',                     'table': 'crop_growth', 'color': '#795548'},
    'DryYield':     {'label': 'Dry Yield (t/ha)',                   'table': 'crop_growth', 'color': '#c0392b'},
}

#: Catalogue of the climate forcing variables. Each key matches both a NetCDF
#: variable name and the ``<Variable>`` part of the filename in
#: :data:`PROCESSED_DIR`. Each value carries ``label`` (daily axis),
#: ``map_label`` (the choropleth reduces over the period, so its units differ),
#: ``unit``, ``color``, and ``colorscale``.
CLIMATE_VARIABLES = {
    'MaxTemp':       {'label': 'Max Temperature (°C)',    'map_label': 'Max Temperature (°C)',    'unit': '°C',      'color': '#e74c3c', 'colorscale': 'RdYlBu_r'},
    'MinTemp':       {'label': 'Min Temperature (°C)',    'map_label': 'Min Temperature (°C)',    'unit': '°C',      'color': '#3498db', 'colorscale': 'RdYlBu_r'},
    'Precipitation': {'label': 'Precipitation (mm/day)', 'map_label': 'Precipitation (mm/year)', 'unit': 'mm/year', 'color': '#2980b9', 'colorscale': 'Blues'   },
    'ReferenceET':   {'label': 'Reference ET (mm/day)',  'map_label': 'Reference ET (mm/year)',  'unit': 'mm/year', 'color': '#e67e22', 'colorscale': 'YlOrBr'  },
}

#: Maps the irrigation names used in the simulation output to the two-letter
#: codes used in the crop-calendar and SPAM variable names. Shared by
#: :func:`~geoaquacrop_plotting.queries.spam_vars_for_crop`,
#: :func:`~geoaquacrop_plotting.queries.get_cropcal_summary`, and
#: :func:`~geoaquacrop_plotting.figures_timeseries.build_input_ts`.
IRR_MAP = {'rainfed': 'rf', 'irrigated': 'ir'}
