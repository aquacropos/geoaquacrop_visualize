"""User configuration: file paths, canvas sizes, and variable catalogues.

Every path is resolved from the workspace root, which is taken from
``GEOAQUACROP_ROOT`` and defaults to the current working directory. Each
individual location can be overridden on its own if it sits elsewhere.

The module reads the environment once, when it is first imported, so anything
that needs to influence the paths must set the variables before that happens.
:func:`geoaquacrop_visualize.build_app` does exactly that, which is why it is
the only supported way to point the app at a workspace.
"""

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                        USER CONFIGURATION                                  ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

import glob
import os

# ── Data locations ────────────────────────────────────────────────────────────
# ROOT is the workspace produced by geoaquacrop_preprocess and
# geoaquacrop_simulate. The three input locations and the export location all
# sit under it unless individually overridden.

#: Workspace root. All other locations default to subdirectories of this.
ROOT          = os.environ.get('GEOAQUACROP_ROOT', os.getcwd())

#: Simulation results written by ``geoaquacrop_simulate``.
OUTPUTS_DIR   = os.environ.get('GEOAQUACROP_OUTPUTS',
                               os.path.join(ROOT, 'outputs'))

#: Preprocessed NetCDF inputs written by ``geoaquacrop_preprocess``.
PROCESSED_DIR = os.environ.get('GEOAQUACROP_PROCESSED',
                               os.path.join(ROOT, 'processed'))

#: Region boundary used for the map outline.
GEOJSON_PATH  = os.environ.get('GEOAQUACROP_REGION',
                               os.path.join(ROOT, 'region.geojson'))

#: Where exports are written. Created by :func:`build_app`, not on import.
EXPORT_DIR    = os.environ.get('GEOAQUACROP_EXPORTS',
                               os.path.join(ROOT, 'outputs', 'exports'))


def _newest(pattern, fallback):
    """Return the last match for ``pattern`` by name, or ``fallback`` if none."""
    matches = sorted(glob.glob(pattern))
    return matches[-1] if matches else fallback


#: Seasonal per-cell results, as a pickled list of DataFrames. The filename
#: carries the timestamp of the simulation run; the most recent is used.
SUMMARY_PKL = _newest(os.path.join(OUTPUTS_DIR, 'summary_results_*.pkl'),
                      os.path.join(OUTPUTS_DIR, 'summary_results.pkl'))

#: Daily per-cell results, as a pickled list of dicts, each holding a
#: ``water_flux`` and a ``crop_growth`` table. Must come from the same run as
#: :data:`SUMMARY_PKL`.
DAILY_PKL   = _newest(os.path.join(OUTPUTS_DIR, 'daily_results_*.pkl'),
                      os.path.join(OUTPUTS_DIR, 'daily_results.pkl'))


#: Grid cell resolution in decimal degrees. Must match the preprocessing grid:
#: ``grid`` draws each cell as a square of this size centred on the cell
#: coordinates, so a mismatch produces overlapping or gapped polygons.
CELL_RES      = float(os.environ.get('GEOAQUACROP_CELL_RES', 0.05))

#: TCP port the Dash server listens on.
PORT          = int(os.environ.get('GEOAQUACROP_PORT', 8050))

#: Height in pixels of the two choropleth map panels. Also the default canvas
#: height used by :func:`~geoaquacrop_visualize.utils.get_auto_zoom`.
MAP_HEIGHT    = 550

#: Height in pixels of the two time-series panels.
TS_HEIGHT     = 400

# ── Region boundary overlay ───────────────────────────────────────────────────
# GEOJSON_PATH is the only source of the outline. At high MB it is far too heavy
# to hand to Plotly, so boundary.py thins it in memory at startup and serves the
# result from BOUNDARY_URL; nothing is written to disk.

#: Ramer-Douglas-Peucker tolerance in decimal degrees (~400 m at these
#: latitudes, invisible at basin zoom) applied to the outline at startup.
#: Raise it for a coarser, lighter outline; lower it for a crisper, heavier one.
BOUNDARY_SIMPLIFY_EPS = 0.004

#: Path the thinned outline is served from on the Dash server. ``boundary``
#: registers the route here and
#: :func:`~geoaquacrop_visualize.queries.mapbox_layers` points the map layer at
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
#: :func:`~geoaquacrop_visualize.queries.spam_vars_for_crop`,
#: :func:`~geoaquacrop_visualize.queries.get_cropcal_summary`, and
#: :func:`~geoaquacrop_visualize.figures_timeseries.build_input_ts`.
IRR_MAP = {'rainfed': 'rf', 'irrigated': 'ir'}
