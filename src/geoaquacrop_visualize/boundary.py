"""The region boundary overlay: derived from GEOJSON_PATH, served by URL.

The outline at :data:`~geoaquacrop_visualize.config.GEOJSON_PATH` is the single
source of truth, but at high MB of raw geometry it cannot be handed to Plotly
directly: Plotly copies whatever geometry it is given into the figure at
construction time, so a module-level dict would be serialised into every map on
every rebuild — six figures, rebuilt on every control change.

So the outline is thinned once at import (``data.region_geojson`` is already in
memory, no second read of the file) and registered as a single static route on
the Dash server. Figures reference it by URL, which is what keeps the geometry
out of the figure payload entirely: the browser fetches it once and caches it.

Nothing is written to disk. The simplified copy lives only in memory and is
rebuilt from GEOJSON_PATH at every startup, so it cannot go stale when the
region outline changes.
"""

import json

from .app_shell import app
from .config import BOUNDARY_SIMPLIFY_EPS, BOUNDARY_URL
from .data import region_geojson
from .utils import simplify_geojson

#: The thinned outline, as a GeoJSON FeatureCollection. Available to any code
#: that wants the geometry itself; ``data.region_geojson`` remains the exact,
#: full-resolution version.
boundary_geojson = simplify_geojson(region_geojson, BOUNDARY_SIMPLIFY_EPS)

# Serialised once, at import, and handed out verbatim on every request. The
# separators drop the whitespace json.dumps would otherwise insert.
_BOUNDARY_BODY = json.dumps(boundary_geojson, separators=(',', ':'))


@app.server.route(BOUNDARY_URL)
def serve_region_boundary():
    """
    Serve the simplified region outline to the browser.

    Registered on the Dash Flask server at
    :data:`~geoaquacrop_visualize.config.BOUNDARY_URL` when this module is
    imported, which happens before the server starts. The response body is
    pre-serialised, so a request costs no work beyond the transfer, and the
    long ``Cache-Control`` lifetime means a session fetches it once however
    many maps are drawn.

    Returns
    -------
    tuple
        A Flask response triple of ``(body, status, headers)``.
    """

    return _BOUNDARY_BODY, 200, {
        'Content-Type': 'application/geo+json',
        'Cache-Control': 'public, max-age=86400',
    }


_rings = sum(len(f['geometry']['coordinates']) for f in boundary_geojson['features'])
_vertices = sum(len(r) for f in boundary_geojson['features']
                for r in f['geometry']['coordinates'])
print(f'Region boundary: {len(boundary_geojson["features"])} polygons, '
      f'{_rings} rings, {_vertices} vertices, '
      f'{len(_BOUNDARY_BODY) / 1e6:.2f} MB served from {BOUNDARY_URL}')
