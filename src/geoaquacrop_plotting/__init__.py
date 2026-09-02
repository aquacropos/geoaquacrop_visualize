"""GeoAquaCrop Visualizer -- an interactive Dash app for gridded AquaCrop runs.

Importing this package builds the whole application: it loads the datasets,
pre-computes the aggregations, assembles ``app.layout``, and registers every
callback. Afterwards ``app`` is ready to serve.

Typical use::

    from geoaquacrop_plotting import app, PORT
    app.run(debug=False, port=PORT)

Module map
----------
config               User configuration and variable catalogues.
utils                Stateless helpers (zoom, colour, date clamping).
data                 One-time dataset loading and derived lookup tables.
grid                 Choropleth GeoJSON, map centre, auto zoom.
boundary             Region outline, thinned at startup and served by URL.
aggregates           Startup pre-computation of per-cell aggregations.
queries              Read-only accessors over the loaded datasets.
export               NetCDF / GeoTIFF / CSV gridded export.
figures_maps         Choropleth figure builders.
figures_timeseries   Time-series figure builders.
styles               Style constants and small layout widgets.
app_shell            The Dash object and HTML index template.
layout_sidebar       Left sidebar column.
layout_panels        Right canvas column.
layout_export        Export modal.
layout               Layout assembly.
callbacks_*          Callback registration, grouped by concern.
"""

from .config import (
    PORT, MAP_HEIGHT, TS_HEIGHT, CELL_RES, EXPORT_DIR,
    MAP_VARIABLES, DAILY_VARIABLES, CLIMATE_VARIABLES,
)
from .app_shell import app

# Layout first, then the callbacks that reference its component ids.
from . import layout  # noqa: F401  (imported for its side effect)
from . import (  # noqa: F401  (imported to register callbacks)
    callbacks_controls,
    callbacks_selection,
    callbacks_maps,
    callbacks_timeseries,
    callbacks_export,
)

__all__ = ['app', 'PORT']


