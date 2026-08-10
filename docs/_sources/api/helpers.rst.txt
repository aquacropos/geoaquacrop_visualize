Helper Functions
================

These pure utility functions are used throughout the figure builders and
callbacks.  They do not modify global state.

.. contents::
   :local:
   :depth: 1

Data retrieval
--------------

get_daily
~~~~~~~~~

Retrieve daily water-flux and crop-growth DataFrames for a single
simulation cell.

**Signature**

.. code-block:: python

   get_daily(cell_id: int) -> tuple[pd.DataFrame | None, pd.DataFrame | None]

**Parameters**

- **cell_id** (*int*) — Integer cell identifier as stored in ``cell_meta``.

**Returns**

A ``(wf, cg)`` tuple:

- **wf** (*pandas.DataFrame | None*) — Daily water-flux table with a
  ``date`` column added. Columns: ``Es``, ``EsPot``, ``Tr``, ``TrPot``,
  ``Infl``, ``Runoff``, ``DeepPerc``, ``Wr``, ``season_counter``.
  Returns ``None`` if the cell is not found or its data is missing.
- **cg** (*pandas.DataFrame | None*) — Daily crop-growth table with a
  ``date`` column added. Columns: ``biomass``, ``canopy_cover``,
  ``gdd_cum``, ``z_root``, ``DryYield``.

get_climate_series
~~~~~~~~~~~~~~~~~~

Extract a daily climate time series at the nearest grid point to a
given coordinate.

**Signature**

.. code-block:: python

   get_climate_series(var: str, x: float, y: float) -> pd.DataFrame | None

**Parameters**

- **var** (*str*) — Climate variable name, e.g. ``'Precipitation'``.
- **x** (*float*) — Longitude in decimal degrees.
- **y** (*float*) — Latitude in decimal degrees.

**Returns**

Two-column ``DataFrame`` with columns ``['date', var]``, or ``None`` if
the variable is not loaded.

get_climate_map_values
~~~~~~~~~~~~~~~~~~~~~~

Compute spatially aggregated climate values for choropleth display.

**Signature**

.. code-block:: python

   get_climate_map_values(var: str, season_label: str) -> xr.DataArray | None

**Parameters**

- **var** (*str*) — Climate variable name.
- **season_label** (*str*) — ``'all'`` for the full simulation period, or
  a four-digit year string (e.g. ``'2008'``).

**Returns**

2-D spatial ``DataArray`` with dimensions ``(y, x)``, or ``None`` if the
variable is not loaded.

get_cropcal_values
~~~~~~~~~~~~~~~~~~

Extract a single scalar value from the crop calendar dataset at a
coordinate.

**Signature**

.. code-block:: python

   get_cropcal_values(var_name: str, x: float, y: float) -> float | None

**Parameters**

- **var_name** (*str*) — Variable in ``cropcal_ds``, e.g.
  ``'Maize_rf_planting'``.
- **x** (*float*) — Longitude in decimal degrees.
- **y** (*float*) — Latitude in decimal degrees.

**Returns**

Nearest-neighbour value, or ``None`` if the variable is absent.

get_cropcal_summary
~~~~~~~~~~~~~~~~~~~

Extract crop calendar information (planting date, season length, harvest
date) for a given crop/irrigation combination.

**Signature**

.. code-block:: python

   get_cropcal_summary(crop_irr: str) -> dict | None

**Parameters**

- **crop_irr** (*str*) — String in the format ``'CropName | irrigation'``,
  e.g. ``'Maize | rainfed'``.

**Returns**

``dict`` with keys ``planting`` (str), ``planting_doy`` (int),
``season_length`` (int | None), ``harvest`` (str); or ``None`` if the crop
is not found.

spam_vars_for_crop
~~~~~~~~~~~~~~~~~~

Find SPAM physical area variable names matching a crop and irrigation type.

**Signature**

.. code-block:: python

   spam_vars_for_crop(crop_irr: str) -> list[str]

**Parameters**

- **crop_irr** (*str*) — Crop/irrigation string, e.g. ``'Maize | rainfed'``.

**Returns**

List of matching SPAM variable names (at most one element), or an empty
list if no match is found.

Colour utilities
----------------

hex_to_rgba
~~~~~~~~~~~

Convert a CSS hex colour to an ``rgba()`` string.

**Signature**

.. code-block:: python

   hex_to_rgba(hex_color: str, alpha: float) -> str

**Parameters**

- **hex_color** (*str*) — Six-character hex with leading ``#``,
  e.g. ``'#2980b9'``.
- **alpha** (*float*) — Opacity between 0.0 and 1.0.

**Returns**

``'rgba(r, g, b, alpha)'`` string.

**Example**

.. code-block:: python

   >>> hex_to_rgba('#ff0000', 0.5)
   'rgba(255,0,0,0.5)'

Date utilities
--------------

safe_date
~~~~~~~~~

Construct a ``Timestamp``, clamping the day to the valid range for the
month.

**Signature**

.. code-block:: python

   safe_date(year: int, month: int, day: int) -> pd.Timestamp

**Parameters**

- **year** (*int*) — Four-digit year.
- **month** (*int*) — Month (1–12).
- **day** (*int*) — Requested day; clamped if too large.

**Returns**

Valid ``pandas.Timestamp``.

**Example**

.. code-block:: python

   >>> safe_date(2008, 2, 31)
   Timestamp('2008-02-29 00:00:00')

Map utilities
-------------

get_auto_zoom
~~~~~~~~~~~~~

Compute an appropriate Mapbox zoom level for a spatial bounding box.

**Signature**

.. code-block:: python

   get_auto_zoom(min_lon, max_lon, min_lat, max_lat,
                 map_width_px=1300, map_height_px=MAP_HEIGHT) -> float

**Parameters**

- **min_lon, max_lon** (*float*) — West / east boundary longitudes.
- **min_lat, max_lat** (*float*) — South / north boundary latitudes.
- **map_width_px** (*int*, optional) — Canvas width in pixels. Default 1300.
- **map_height_px** (*int*, optional) — Canvas height in pixels. Default
  ``MAP_HEIGHT``.

**Returns**

Zoom level (float, rounded to 1 decimal place), with a 0.5 margin subtracted.

mapbox_layers
~~~~~~~~~~~~~

Build the Mapbox layer stack (ESRI topo raster + region boundary line)
used by all map figures.

**Signature**

.. code-block:: python

   mapbox_layers() -> list[dict]

**Returns**

Two-element list of Mapbox layer specification dicts.

UI helpers
----------

btn_style
~~~~~~~~~

Generate an inline style dict for a toggle button.

**Signature**

.. code-block:: python

   btn_style(active: bool, color: str) -> dict

**Parameters**

- **active** (*bool*) — If ``True``, filled background; otherwise light.
- **color** (*str*) — Palette key: ``'blue'``, ``'green'``, ``'orange'``,
  ``'purple'``, ``'teal'``, or ``'red'``.

dd_style
~~~~~~~~

Generate an inline style dict for an inline dropdown component.

**Signature**

.. code-block:: python

   dd_style(w: str = '80px') -> dict

**Parameters**

- **w** (*str*, optional) — CSS width string. Default ``'80px'``.
