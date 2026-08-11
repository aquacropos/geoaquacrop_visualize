Figure Builders
===============

These functions construct complete Plotly figures.  They are called from
callbacks and from the initial ``app.layout`` definition.

.. contents::
   :local:
   :depth: 1

build_output_map
----------------

Build the simulation output choropleth map.

**Signature**

.. code-block:: python

   build_output_map(
       ci: str,
       season: str,
       map_var: str,
       agg_override: str,
       sel_cell: int | None = None,
       lasso_cells: list[int] | None = None,
       relayout_data: dict | None = None,
   ) -> go.Figure

**Parameters**

- **ci** (*str*) — Crop/irrigation string, e.g. ``'Maize | rainfed'``.
- **season** (*str*) — Year string (e.g. ``'2008'``) or ``'all'``.
- **map_var** (*str*) — Key from :data:`MAP_VARIABLES`.
- **agg_override** (*str*) — ``'mean'`` or ``'sum'`` (used when
  ``season='all'``).
- **sel_cell** (*int | None*) — Cell ID to highlight in blue.
- **lasso_cells** (*list[int] | None*) — Cell IDs to highlight in orange.
- **relayout_data** (*dict | None*) — Mapbox relayout event data to
  preserve zoom and centre.

**Returns**

Five-trace Plotly figure:

1. Grey background tile (all cells).
2. Coloured choropleth for the selected variable.
3. Blue highlight for the clicked cell.
4. Orange highlight for lasso-selected cells.
5. Invisible scatter layer for lasso-tool support.

build_output_ts
---------------

Build the daily output time series figure.

**Signature**

.. code-block:: python

   build_output_ts(
       cell_id: int | None,
       season_label: str,
       daily_var: str,
       ts_period: str,
       ts_clicks: dict | None = None,
   ) -> go.Figure

**Parameters**

- **cell_id** (*int | None*) — Cell to plot; ``None`` returns a placeholder.
- **season_label** (*str*) — Year string or ``'all'``.
- **daily_var** (*str*) — Key from :data:`DAILY_VARIABLES`.
- **ts_period** (*str*) — ``'season'`` or ``'full'``.
- **ts_clicks** (*dict | None*) — Click state with keys ``count``,
  ``start``, ``end`` for the mean ± std window tool.

**Returns**

Line chart with optional pre-season shading and mean ± std band.

build_input_map
---------------

Build the climate input choropleth map.

**Signature**

.. code-block:: python

   build_input_map(
       climate_var: str,
       season_label: str,
       sel_cell: int | None = None,
       relayout_data: dict | None = None,
   ) -> go.Figure

**Parameters**

- **climate_var** (*str*) — Key from :data:`CLIMATE_VARIABLES`.
- **season_label** (*str*) — Year string or ``'all'``.
- **sel_cell** (*int | None*) — Cell ID to highlight in blue.
- **relayout_data** (*dict | None*) — Mapbox relayout data.

**Returns**

Three-trace Plotly figure: grey background, climate choropleth, click
highlight.

build_spam_map
--------------

Build the SPAM crop physical area choropleth map.

**Signature**

.. code-block:: python

   build_spam_map(
       spam_var: str,
       sel_cell: int | None = None,
       relayout_data: dict | None = None,
   ) -> go.Figure

**Parameters**

- **spam_var** (*str*) — SPAM dataset variable name, e.g.
  ``'Maize_rf_physical_area'``.
- **sel_cell** (*int | None*) — Cell to highlight.
- **relayout_data** (*dict | None*) — Mapbox relayout data.

**Returns**

Choropleth of harvested physical area (ha) using YlGn colour scale.

build_input_ts
--------------

Build the climate input daily time series figure.

**Signature**

.. code-block:: python

   build_input_ts(
       cell_id: int | None,
       climate_var: str,
       season_label: str,
       ts_period: str,
       ts_clicks: dict | None = None,
       sel_crop_irr: str | None = None,
   ) -> go.Figure

**Parameters**

- **cell_id** (*int | None*) — Cell to plot; ``None`` returns a placeholder.
- **climate_var** (*str*) — Key from :data:`CLIMATE_VARIABLES`.
- **season_label** (*str*) — Year string or ``'all'``.
- **ts_period** (*str*) — ``'season'`` or ``'full'``.
- **ts_clicks** (*dict | None*) — Click state for mean ± std window.
- **sel_crop_irr** (*str | None*) — Crop/irrigation string used to draw
  planting date vertical lines from the crop calendar.

**Returns**

Line chart with optional pre-season shading, planting date markers, and
mean ± std band.

_add_mean_std_band *(internal)*
-------------------------------

Add a mean ± std shaded band to an existing time series figure.

**Signature**

.. code-block:: python

   _add_mean_std_band(
       fig: go.Figure,
       df_plot: pd.DataFrame,
       var_col: str,
       color: str,
       year_start: pd.Timestamp,
       year_end: pd.Timestamp,
       ts_clicks: dict | None,
   ) -> go.Figure

Reads a two-click window from ``ts_clicks`` and overlays:

- Filled band between mean − std and mean + std.
- Dashed mean line.
- Two vertical boundary markers.
- Annotation box with mean and std values.

When fewer than two clicks have been recorded, instructional annotations
are added instead.
