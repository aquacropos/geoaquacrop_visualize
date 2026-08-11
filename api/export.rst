Export Functions
================

export_data
-----------

Export daily gridded simulation output to NetCDF, GeoTIFF, and/or CSV.

**Signature**

.. code-block:: python

   export_data(
       selected_cells: list[int],
       export_vars: list[str],
       start_date: str,
       end_date: str,
       formats: list[str],
   ) -> str

**Parameters**

- **selected_cells** (*list[int]*) — Cell IDs to include.  Pass
  ``list(cell_meta.keys())`` for the whole simulation area.
- **export_vars** (*list[str]*) — Variable names matching keys in
  :data:`DAILY_VARIABLES`, e.g. ``['Es', 'Tr', 'biomass']``.
- **start_date** (*str*) — ISO 8601 date string for the period start,
  e.g. ``'2008-01-01'``.
- **end_date** (*str*) — ISO 8601 date string for the period end,
  e.g. ``'2010-12-31'``.
- **formats** (*list[str]*) — Output format codes.  Any combination of:

  - ``'nc'`` — NetCDF 4 via xarray.
  - ``'tif'`` — Multi-band GeoTIFF via rasterio *(optional)*.
  - ``'csv'`` — Flat CSV with columns ``date``, ``cell_id``, ``x``,
    ``y``, ``<var>``.

**Returns**

Human-readable status string listing saved filenames and the output
directory, or an error string if the date range is empty or no variables
were exported.

**Notes**

- Each exported variable produces one or more files named
  ``<var>_<YYYYMMDD>_<YYYYMMDD>.<ext>``.
- The NetCDF coordinate reference system is implicitly EPSG:4326
  (geographic).
- GeoTIFF export requires ``rasterio``.  If not installed, a warning is
  appended to the status string and GeoTIFF is skipped.
- Spatial ordering follows the cell grid: x (longitude) increases left to
  right, y (latitude) decreases top to bottom.

**Example**

.. code-block:: python

   msg = export_data(
       selected_cells=[1001, 1002, 1003],
       export_vars=['Tr', 'biomass'],
       start_date='2008-05-01',
       end_date='2008-09-30',
       formats=['nc', 'csv'],
   )
   print(msg)
   # Saved 4 file(s) to /path/to/exports: Tr_20080501_20080930.nc,
   # Tr_20080501_20080930.csv, biomass_20080501_20080930.nc,
   # biomass_20080501_20080930.csv
