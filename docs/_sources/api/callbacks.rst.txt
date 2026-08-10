Dash Callbacks
==============

All Dash callbacks are defined after the ``app.layout`` block.  They use
:data:`dcc.Store` components as a central state bus so that each callback
reads from stores rather than from other components directly.

.. contents::
   :local:
   :depth: 1

Store components (state bus)
-----------------------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Store ID
     - Purpose
   * - ``sel-tab``
     - Active tab (``'output'`` or ``'input'``).
   * - ``sel-crop``
     - Selected crop/irrigation string.
   * - ``sel-season``
     - Selected season year or ``'all'``.
   * - ``sel-map-var``
     - Active map variable key.
   * - ``sel-daily-var``
     - Active daily variable key.
   * - ``sel-clim-var``
     - Active climate variable key.
   * - ``sel-agg``
     - Aggregation function (``'mean'`` or ``'sum'``).
   * - ``sel-out-cell``
     - Cell ID clicked on the output map.
   * - ``sel-in-cell``
     - Cell ID clicked on the input map.
   * - ``out-ts-clicks``
     - Click state for output time series mean ± std window.
   * - ``in-ts-clicks``
     - Click state for input time series mean ± std window.
   * - ``lasso-cells``
     - Cell IDs selected by lasso / box on the output map.
   * - ``sel-spam-var``
     - Active SPAM variable key.
   * - ``input-mode``
     - Input map mode: ``'climate'`` or ``'spam'``.
   * - ``export-vars``
     - Merged list of selected export variable keys.

Tab management
--------------

set_tab
~~~~~~~
*Input:* ``main-tabs.value``

Stores the active tab name in ``sel-tab``.

toggle_tabs
~~~~~~~~~~~
*Input:* ``sel-tab.data``

Shows/hides the output panel + controls vs. input panel + controls.

Variable selection
------------------

set_crop / set_season / set_clim_var
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Simple pass-through callbacks that copy dropdown values into the
corresponding stores.

set_map_var
~~~~~~~~~~~
*Inputs:* three accordion dropdowns (yield, water, water-productivity)

Merges the three dropdowns into ``sel-map-var`` and clears the other two
so only one variable is active at a time.

set_daily_var
~~~~~~~~~~~~~
*Inputs:* three accordion dropdowns (flux, soil, crop)

Same mutex logic as ``set_map_var`` for the daily variable group.

set_agg / style_agg_btns / toggle_agg_row
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Manage the mean / sum aggregation toggle buttons.

Cell selection
--------------

set_out_cell / set_in_cell
~~~~~~~~~~~~~~~~~~~~~~~~~~
*Input:* ``output-map.clickData`` / ``input-map.clickData``

Extracts the ``location`` field from the Plotly choropleth click event and
stores it as an integer cell ID.

Lasso selection
---------------

handle_lasso
~~~~~~~~~~~~
*Input:* ``output-map.selectedData``, ``export-whole-area.value``

Extracts cell IDs from the invisible scatter layer's ``text`` attribute.
Clears the selection when *Whole area* is checked.

Map updates (Patch-based)
--------------------------

patch_output_map_data
~~~~~~~~~~~~~~~~~~~~~
*Inputs:* ``sel-crop``, ``sel-season``, ``sel-map-var``, ``sel-agg``

Uses :class:`dash.Patch` to update only the choropleth z-values,
locations, colour scale, colour-bar title, and hover text.  The GeoJSON
geometry remains in the browser, so updates are fast.

patch_output_map_highlights
~~~~~~~~~~~~~~~~~~~~~~~~~~~
*Inputs:* ``sel-out-cell``, ``lasso-cells``

Updates trace indices 2 (clicked cell, blue) and 3 (lasso cells, orange)
via Patch.

patch_input_map_data
~~~~~~~~~~~~~~~~~~~~
*Inputs:* ``sel-clim-var``, ``sel-spam-var``, ``input-mode``,
``sel-season``

Handles both climate and SPAM modes.  In climate mode updates z-values
from the aggregated climate grid; in SPAM mode updates from the SPAM
physical area dataset.

patch_input_map_highlight
~~~~~~~~~~~~~~~~~~~~~~~~~
*Input:* ``sel-in-cell``

Updates trace index 2 (clicked cell, blue) via Patch.

Time series updates
-------------------

update_output_ts
~~~~~~~~~~~~~~~~
*Inputs:* ``sel-out-cell``, ``sel-season``, ``sel-daily-var``,
``out-ts-clicks``

Calls :func:`build_output_ts` and controls the container visibility.

update_input_ts
~~~~~~~~~~~~~~~
*Inputs:* ``sel-in-cell``, ``sel-clim-var``, ``sel-season``,
``in-ts-clicks``, ``sel-crop``

Calls :func:`build_input_ts` and controls the container visibility.

Time series click tool
----------------------

_handle_click *(internal)*
~~~~~~~~~~~~~~~~~~~~~~~~~~
Three-state cycle: first click sets the start date, second sets the end
(auto-sorted), third resets.

handle_out_ts_click / handle_in_ts_click
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Delegate to :func:`_handle_click` for the respective time series.

reset_out_clicks / reset_in_clicks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Reset the click state when cell, season, or variable changes.

Ribbon text
-----------

update_ts_ribbon_text
~~~~~~~~~~~~~~~~~~~~~
Shows cell coordinates, crop, and season above the output time series.

update_input_ribbon_text
~~~~~~~~~~~~~~~~~~~~~~~~
Shows cell coordinates, climate variable, and season above the input time
series.

Crop calendar info
------------------

update_cropcal_info
~~~~~~~~~~~~~~~~~~~
*Inputs:* ``sel-crop``, ``sel-tab``

Calls :func:`get_cropcal_summary` and formats a one-line summary above the
input map.

SPAM buttons
------------

update_spam_buttons
~~~~~~~~~~~~~~~~~~~
*Inputs:* ``sel-crop``, SPAM button clicks, ``climvar-dd.value``

Rebuilds the SPAM button list for the selected crop.  Sets ``input-mode``
to ``'spam'`` on a SPAM click or back to ``'climate'`` when the climate
dropdown is changed.

Export
------

run_export
~~~~~~~~~~
*Input:* ``export-btn.n_clicks``

Validates selections, resolves the date range and cell list, then calls
:func:`export_data`.  Returns a status string shown in the modal footer.

toggle_export_modal
~~~~~~~~~~~~~~~~~~~
Toggles the export modal open/closed.

toggle_export_btn
~~~~~~~~~~~~~~~~~
Shows the Export button only on the *Simulation Outputs* tab.

merge_export_vars
~~~~~~~~~~~~~~~~~
Merges the three export checklists (flux, soil, crop) into the
``export-vars`` store.

toggle_date_dropdowns
~~~~~~~~~~~~~~~~~~~~~
Disables the date dropdowns when *Whole simulation* is checked.

constrain_end_date
~~~~~~~~~~~~~~~~~~
*Inputs:* start-year, start-month, start-day dropdowns

Filters end-date options so the export end date cannot precede the start.
Clamps selected values if they fall outside the new valid range.
