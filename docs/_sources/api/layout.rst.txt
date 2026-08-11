App Layout
==========

The Dash application layout is defined as a
:class:`dash_bootstrap_components.Container` (``fluid=True``) containing
one main row split into a left sidebar (3 columns) and a right canvas
(9 columns).

.. contents::
   :local:
   :depth: 1

Left sidebar
------------

The sidebar carries all user controls.  It is divided into the following
sections:

Title
~~~~~
``html.H5`` with the application title *GeoAquaCrop Explorer*.

Tab bar
~~~~~~~
``dcc.Tabs`` with two tabs:

- **Simulation Outputs** — shows the output panel and output controls.
- **Inputs** — shows the input panel and input controls.

Data Configuration section
~~~~~~~~~~~~~~~~~~~~~~~~~~
Two dropdowns shared between both tabs:

- **Crop & Irrigation** (``crop-dropdown``) — lists all unique
  crop/irrigation combinations found in the summary data.
- **Season** (``season-dropdown``) — lists all harvest years plus an
  *All years* option.
- **Aggregation row** (``agg-row``) — mean/sum toggle, shown only when
  *All years* is selected on the Outputs tab.

Output controls (``output-controls``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Visible only on the *Simulation Outputs* tab.

**Map Variable** — Accordion with three groups:

- *Yield & Production* → ``mapvar-yield-dd``
- *Water Balance* → ``mapvar-water-dd``
- *Water Productivity* → ``mapvar-wp-dd``

**Daily Variable** — Accordion with three groups:

- *Water Fluxes* → ``dailyvar-flux-dd``
- *Soil Water* → ``dailyvar-soil-dd``
- *Crop Development* → ``dailyvar-crop-dd``

Input controls (``input-controls``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Visible only on the *Inputs* tab.

- **Climate Variable** (``climvar-dd``) — four options from
  :data:`CLIMATE_VARIABLES`.
- **Crop Area (SPAM)** (``spam-btn-container``) — dynamically generated
  buttons for matching SPAM variables.

Export button
~~~~~~~~~~~~~
Pinned to the bottom of the sidebar (absolute positioning).  Opens the
export modal.

Right canvas
------------

Output panel (``output-panel``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- ``output-map`` — simulation output choropleth (
  :func:`build_output_map`).
- ``output-ts-container`` — collapsible ribbon + line chart
  (:func:`build_output_ts`), shown after a cell is clicked.

Input panel (``input-panel``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- Crop-calendar info bar (``cropcal-info-text``).
- ``input-map`` — climate / SPAM choropleth (:func:`build_input_map`).
- ``input-ts-container`` — collapsible ribbon + line chart
  (:func:`build_input_ts`), shown after a cell is clicked.

Export modal
------------

``dbc.Modal`` (id ``export-modal``, large size) contains:

- Variable checklists grouped by Water Fluxes / Soil Water / Crop
  Development.
- Period row: *Whole simulation* checkbox + year/month/day dropdowns for
  start and end.
- Cells row: *Whole area* checkbox + lasso cell count label.
- Format checklist: NetCDF, GeoTIFF, CSV.
- Footer: status text + *Export* button + *Close* button.

Style constants
---------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Name
     - Value / Description
   * - ``FONT_STACK``
     - ``'Arial, system-ui, -apple-system, sans-serif'``
   * - ``ACCENT``
     - ``'#a6c1eb'`` — blue used for tab highlights and the export button.
   * - ``SIDEBAR_BG``
     - ``'#f8f9fa'`` — light grey sidebar background.
   * - ``SIDEBAR_STYLE``
     - Full CSS dict for the sidebar column.
   * - ``RIBBON_STYLE``
     - CSS dict for the info ribbon strip above time series panels.
   * - ``DD_CTRL_STYLE``
     - Minimal CSS for in-sidebar dropdown components.

Layout helper functions
-----------------------

_sec_hdr(text)
~~~~~~~~~~~~~~
Returns a styled ``html.Div`` used as a section header in the sidebar
(uppercase, bold, black).

_ctrl_label(text)
~~~~~~~~~~~~~~~~~
Returns a styled ``html.Label`` displayed above a dropdown control.

_map_dd_opts(keys)
~~~~~~~~~~~~~~~~~~
Builds ``[{'label': ..., 'value': ...}]`` option dicts for a subset of
:data:`MAP_VARIABLES` keys.

_daily_dd_opts(keys)
~~~~~~~~~~~~~~~~~~~~
Same as ``_map_dd_opts`` but for :data:`DAILY_VARIABLES` keys.
