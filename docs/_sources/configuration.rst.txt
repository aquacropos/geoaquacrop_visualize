Configuration
=============

All user-facing settings live in the **USER CONFIGURATION** block at the
top of ``aquacropgrid_plots_v2.py``.

Path constants
--------------

.. code-block:: python

   SUMMARY_PKL   = '../high_plains_package/outputs/summary_results_*.pkl'
   DAILY_PKL     = '../high_plains_package/outputs/daily_results_*.pkl'
   GEOJSON_PATH  = '../high_plains_package/inputdata/high_plains/high_plains.geojson'
   PROCESSED_DIR = '../high_plains_package/processed'
   EXPORT_DIR    = '../high_plains_package/outputs/exports'

All paths are resolved relative to the script location using
:py:func:`os.path.abspath`, so the application can be launched from any
working directory.

Display constants
-----------------

.. list-table::
   :header-rows: 1
   :widths: 25 15 60

   * - Constant
     - Default
     - Description
   * - ``CELL_RES``
     - ``0.05``
     - Grid cell resolution in decimal degrees. Must match the
       preprocessing step.
   * - ``PORT``
     - ``8050``
     - TCP port for the Dash development server.
   * - ``MAP_HEIGHT``
     - ``550``
     - Height in pixels of the choropleth map panels.
   * - ``TS_HEIGHT``
     - ``400``
     - Height in pixels of the time series panels.

Variable registries
-------------------

Three module-level dictionaries define which variables are available in
the UI and how they are displayed.

MAP_VARIABLES
~~~~~~~~~~~~~

Controls the simulation output choropleth map.  Each key is a column name
in the summary pickle.  Each value is a dict with:

- ``label`` — display name used in the colour bar and dropdowns.
- ``colorscale`` — Plotly colour scale for mean aggregation.
- ``sum_colorscale`` — Plotly colour scale for sum aggregation.
- ``default_agg`` — default aggregation when *All years* is selected
  (``'mean'`` or ``'sum'``).

DAILY_VARIABLES
~~~~~~~~~~~~~~~

Controls the daily time series panel.  Each key is a column name in the
daily pickle tables.  Each value is a dict with:

- ``label`` — display name.
- ``table`` — source table, either ``'water_flux'`` or ``'crop_growth'``.
- ``color`` — hex colour for the line trace.

CLIMATE_VARIABLES
~~~~~~~~~~~~~~~~~

Controls the climate input choropleth and time series.  Each key matches a
NetCDF variable name.  Each value is a dict with:

- ``label`` — daily y-axis label (e.g. ``'Precipitation (mm/day)'``).
- ``map_label`` — choropleth hover label (e.g. ``'Precipitation (mm/year)'``).
- ``unit`` — colour bar unit string.
- ``color`` — hex colour for the time series line.
- ``colorscale`` — Plotly colour scale for the choropleth.
