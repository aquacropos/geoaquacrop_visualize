# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                        GEOAQUACROP VISUALIZER — ENTRY POINT                ║
# ╚══════════════════════════════════════════════════════════════════════════════╝
"""Launch the GeoAquaCrop Visualizer Dash application.

The application itself lives in the ``geoaquacrop_plotting`` package, split by
concern so that no module exceeds a few hundred lines:

    geoaquacrop_plotting/
        config.py               USER CONFIGURATION — edit paths and sizes here
        utils.py                stateless helpers (zoom, colour, date clamping)
        data.py                 one-time dataset loading and lookup tables
        grid.py                 choropleth GeoJSON, map centre, auto zoom
        aggregates.py           startup pre-computation of per-cell aggregations
        queries.py              read-only accessors over the loaded datasets
        export.py               NetCDF / GeoTIFF / CSV gridded export
        figures_maps.py         choropleth figure builders
        figures_timeseries.py   time-series figure builders
        styles.py               style constants and small layout widgets
        app_shell.py            the Dash object and HTML index template
        layout_sidebar.py       left sidebar column
        layout_panels.py        right canvas column
        layout_export.py        export modal
        layout.py               layout assembly
        callbacks_controls.py   sidebar control callbacks
        callbacks_selection.py  cell/lasso/time-window selection callbacks
        callbacks_maps.py       map patching callbacks
        callbacks_timeseries.py time-series rebuild callbacks
        callbacks_export.py     export modal callbacks

Importing the package loads every dataset once, pre-computes all aggregations,
assembles the layout, and registers all callbacks — exactly as the previous
single-file version did on import.

Usage
-----
    python geoaquacrop_plots.py

or, once the project is pip-installed::

    geoaquacrop-visualizer

Then open http://localhost:8050 in a browser.

To configure paths, edit ``geoaquacrop_plotting/config.py``.
"""

from geoaquacrop_plotting import app, PORT


def main():
    """Serve the application on the port configured in ``config.PORT``."""

    app.run(debug=False, port=PORT)


if __name__ == '__main__':
    main()
