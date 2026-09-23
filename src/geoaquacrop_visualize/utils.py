"""Stateless helper functions that do not touch the loaded datasets."""

import math

import numpy as np
import pandas as pd

from .config import BOUNDARY_SIMPLIFY_EPS, MAP_HEIGHT

def get_auto_zoom(min_lon, max_lon, min_lat, max_lat,
                  map_width_px=1300, map_height_px=MAP_HEIGHT):
    """
    Compute an appropriate Mapbox zoom level for a given spatial extent.

    Uses the Web Mercator tile formula to derive a zoom level that fits the
    bounding box within the specified map canvas size. Falls back to zoom 8.5
    when the spatial extent is degenerate (zero span in either dimension).

    Parameters
    ----------
    min_lon : float
        Western boundary longitude in decimal degrees.
    max_lon : float
        Eastern boundary longitude in decimal degrees.
    min_lat : float
        Southern boundary latitude in decimal degrees.
    max_lat : float
        Northern boundary latitude in decimal degrees.
    map_width_px : int, optional
        Canvas width in pixels used for zoom calculation. Default is 1300.
    map_height_px : int, optional
        Canvas height in pixels used for zoom calculation. Default is MAP_HEIGHT.

    Returns
    -------
    float
        Zoom level rounded to one decimal place, reduced by 0.5 from the
        tile-exact value to add a margin around the extent.
    """
    
    lon_span = max_lon - min_lon
    lat_span = max_lat - min_lat
    if lon_span == 0 or lat_span == 0:
        return 8.5
    zoom_lon = math.log2(360 * map_width_px  / (256 * lon_span))
    zoom_lat = math.log2(180 * map_height_px / (256 * lat_span))
    return round(min(zoom_lon, zoom_lat) - 0.5, 1)

def hex_to_rgba(hex_color, alpha):
    """
    Convert a CSS hex colour string to an ``rgba()`` string.

    Parameters
    ----------
    hex_color : str
        Six-character hex colour with leading ``#``, e.g. ``'#2980b9'``.
    alpha : float
        Opacity value between 0.0 (transparent) and 1.0 (opaque).

    Returns
    -------
    str
        CSS colour string of the form ``'rgba(r, g, b, alpha)'``.

    Examples
    --------
    >>> hex_to_rgba('#ff0000', 0.5)
    'rgba(255,0,0,0.5)'
    """

    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    return f'rgba({r},{g},{b},{alpha})'

def safe_date(year, month, day):
    """
    Construct a Timestamp, clamping the day to the valid range for the month.

    Prevents ``ValueError`` when a day value such as 31 is passed for a month
    with fewer days (e.g. February, April). Used in the export date pickers.

    Parameters
    ----------
    year : int
        Four-digit calendar year.
    month : int
        Month number between 1 and 12.
    day : int
        Requested day number. Clamped to the maximum valid day if too large.

    Returns
    -------
    pandas.Timestamp
        Valid timestamp for the given year and month, with day clamped.

    Examples
    --------
    >>> safe_date(2008, 2, 31)
    Timestamp('2008-02-29 00:00:00')
    """
    import calendar
    max_day = calendar.monthrange(year, month)[1]
    return pd.Timestamp(year=year, month=month, day=min(day, max_day))


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  BOUNDARY SIMPLIFICATION                                                   ║
# ╚══════════════════════════════════════════════════════════════════════════════╝
#
# A pure-numpy Ramer-Douglas-Peucker implementation, kept here rather than in
# boundary.py so it stays importable (and testable) without the dataset. No
# shapely/geopandas dependency is introduced for what is a few dozen lines.

def rdp_keep_mask(points, eps):
    """
    Mark the points an RDP simplification of a polyline would keep.

    Iterative Ramer-Douglas-Peucker: the segment furthest from the straight
    line joining the endpoints is kept if it lies more than ``eps`` away, and
    the two halves either side of it are then processed the same way. The loop
    carries its own stack rather than recursing, so ring length cannot exhaust
    the interpreter's recursion limit.

    Parameters
    ----------
    points : numpy.ndarray
        Vertices as an ``(N, 2)`` float array.
    eps : float
        Tolerance in the units of ``points`` — degrees, for lon/lat input.
        A vertex is dropped when it lies within ``eps`` of the line it would
        otherwise bend.

    Returns
    -------
    numpy.ndarray
        Boolean mask of length ``N``. The first and last points are always
        kept, so the polyline keeps its endpoints.
    """

    n = len(points)
    keep = np.zeros(n, dtype=bool)
    if n == 0:
        return keep
    keep[0] = keep[-1] = True
    stack = [(0, n - 1)]
    while stack:
        i, j = stack.pop()
        if j <= i + 1:                     # nothing between the endpoints
            continue
        start, end = points[i], points[j]
        span = points[i + 1:j] - start
        dx, dy = end - start
        length = math.hypot(dx, dy)
        if length == 0:                    # closed sub-path: use radial distance
            d = np.hypot(span[:, 0], span[:, 1])
        else:                              # 2-D cross product / |line|
            d = np.abs(dx * span[:, 1] - dy * span[:, 0]) / length
        k = int(np.argmax(d))
        if d[k] > eps:
            k += i + 1
            keep[k] = True
            stack.append((i, k))
            stack.append((k, j))
    return keep


def simplify_ring(ring, eps=BOUNDARY_SIMPLIFY_EPS, decimals=5):
    """
    Simplify one polygon ring, keeping it closed and valid.

    Runs :func:`rdp_keep_mask` over the ring, rounds the survivors to
    ``decimals`` places (five is ~1 m at these latitudes, and shortens the
    serialised output considerably), and re-closes the ring if rounding or
    simplification separated its first and last point.

    Parameters
    ----------
    ring : sequence
        Ring vertices, as accepted by ``numpy.asarray`` — an ``(N, 2)``
        sequence of ``[lon, lat]`` pairs.
    eps : float, optional
        RDP tolerance in degrees. Defaults to
        :data:`~geoaquacrop_visualize.config.BOUNDARY_SIMPLIFY_EPS`.
    decimals : int, optional
        Coordinate rounding precision. Default is 5.

    Returns
    -------
    list or None
        The simplified closed ring as a list of ``[lon, lat]`` pairs, or
        ``None`` if it collapsed below the four points a closed ring needs —
        which is what becomes of specks smaller than the tolerance.
    """

    points = np.asarray(ring, dtype=float)
    if points.ndim != 2 or len(points) < 3:
        return None
    out = np.round(points[rdp_keep_mask(points, eps)], decimals).tolist()
    if out[0] != out[-1]:
        out.append(out[0])
    return out if len(out) >= 4 else None


def simplify_geojson(geojson, eps=BOUNDARY_SIMPLIFY_EPS):
    """
    Thin every polygon in a GeoJSON FeatureCollection for use as a line overlay.

    Each ring goes through :func:`simplify_ring`; rings that collapse are
    dropped, and features left with no rings at all disappear with them.
    Properties are discarded — the overlay draws an outline and never reads
    them — as is any ``crs`` member, since GeoJSON is WGS84 by definition.
    MultiPolygons are flattened into one Feature per polygon.

    Parameters
    ----------
    geojson : dict
        A parsed GeoJSON FeatureCollection of Polygon and/or MultiPolygon
        features.
    eps : float, optional
        RDP tolerance in degrees. Defaults to
        :data:`~geoaquacrop_visualize.config.BOUNDARY_SIMPLIFY_EPS`.

    Returns
    -------
    dict
        A new FeatureCollection of property-less Polygon features. The input
        is not modified.
    """

    features = []
    for feature in geojson.get('features', []):
        geometry = feature.get('geometry') or {}
        kind = geometry.get('type')
        if kind == 'Polygon':
            polygons = [geometry.get('coordinates', [])]
        elif kind == 'MultiPolygon':
            polygons = geometry.get('coordinates', [])
        else:
            continue                       # points and lines have no outline
        for rings in polygons:
            kept = [r for r in (simplify_ring(ring, eps) for ring in rings) if r]
            if kept:
                features.append({
                    'type': 'Feature',
                    'properties': {},
                    'geometry': {'type': 'Polygon', 'coordinates': kept},
                })
    return {'type': 'FeatureCollection', 'features': features}
