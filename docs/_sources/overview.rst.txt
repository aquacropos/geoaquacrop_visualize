Overview
========

GeoAquaCrop Visualizer is a single-file Dash application
(``aquacropgrid_plots_v2.py``) that renders an interactive dashboard for
post-processing and exploring gridded AquaCrop-OSPy simulation results.

Features
--------

Simulation Outputs tab
~~~~~~~~~~~~~~~~~~~~~~
- Choropleth map of yield, water-balance, and water-productivity variables.
- Per-season and multi-year aggregated views (mean or sum).
- Lasso / box selection of cells for spatial subsets.
- Daily time series for any selected cell: water fluxes, soil water, and
  crop development.
- Interactive mean ± standard-deviation window tool on time series.

Inputs tab
~~~~~~~~~~
- Choropleth map of maximum/minimum temperature, precipitation, and
  reference ET.
- Per-year or full-period averages.
- Daily climate time series with planting-date overlays from the crop
  calendar.
- SPAM crop-area overlay for rainfed and irrigated extents.

Export
~~~~~~
- Export daily gridded output to NetCDF (``.nc``), GeoTIFF (``.tif``), or
  CSV.
- Flexible date range and spatial subset (whole area or lasso selection).

Architecture
------------

The application is structured in five logical sections inside the single
Python file:

1. **User configuration** — path constants and display options at the top
   of the file.
2. **Data loading** — runs at startup; loads simulation pickle files,
   climate NetCDF grids, the crop calendar, and SPAM crop-area data.
3. **Helper functions** — pure functions for data retrieval and colour
   utilities.
4. **Figure builders** — functions that return Plotly figures for maps and
   time series.
5. **Dash layout and callbacks** — the Dash ``app.layout`` tree and all
   ``@app.callback`` functions that wire UI events to data updates.

Requirements
------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Package
     - Purpose
   * - Python 3.10+
     - Runtime
   * - pandas
     - Data manipulation
   * - numpy
     - Array operations
   * - xarray
     - NetCDF climate files
   * - plotly
     - Interactive figures
   * - dash
     - Web application framework
   * - dash-bootstrap-components
     - Sidebar layout
   * - rasterio *(optional)*
     - GeoTIFF export

Quick start
-----------

.. code-block:: bash

   conda env create -f environment.yml
   conda activate aquacropgrid-preproc
   python aquacropgrid_plots_v2.py

Then open ``http://localhost:8050`` in your browser.

Input data structure
--------------------

The application expects the following preprocessed files in ``PROCESSED_DIR``:

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - File
     - Description
   * - ``MaxTemp<YYYY><YYYY>.nc``
     - Daily maximum temperature grid
   * - ``MinTemp<YYYY><YYYY>.nc``
     - Daily minimum temperature grid
   * - ``Precipitation<YYYY><YYYY>.nc``
     - Daily precipitation grid
   * - ``ReferenceET<YYYY><YYYY>.nc``
     - Daily reference ET grid
   * - ``cropcalendar.nc``
     - Planting DOY and growing season length per crop
   * - ``spam*_physical_area.nc``
     - SPAM crop physical area *(optional)*

Simulation outputs are loaded from two pickle files:

- ``summary_results_*.pkl`` — seasonal aggregated results per cell.
- ``daily_results_*.pkl`` — daily water flux and crop growth tables per
  cell.
