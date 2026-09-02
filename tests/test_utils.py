"""
Tests for ``geoaquacrop_plotting.utils``.

Imports the real functions — utils depends only on config, so these tests
exercise the shipped code rather than a copy of it.
"""

import numpy as np
import pandas as pd
import pytest

from geoaquacrop_plotting.utils import (
    get_auto_zoom, hex_to_rgba, rdp_keep_mask, safe_date, simplify_geojson,
    simplify_ring,
)


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  hex_to_rgba                                                               ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class TestHexToRgba:

    def test_red(self):
        assert hex_to_rgba('#ff0000', 0.5) == 'rgba(255,0,0,0.5)'

    def test_blue(self):
        assert hex_to_rgba('#2980b9', 0.2) == 'rgba(41,128,185,0.2)'

    def test_white(self):
        assert hex_to_rgba('#ffffff', 1.0) == 'rgba(255,255,255,1.0)'

    def test_black(self):
        assert hex_to_rgba('#000000', 0.0) == 'rgba(0,0,0,0.0)'

    def test_uppercase_hex(self):
        assert hex_to_rgba('#FF8000', 0.75) == 'rgba(255,128,0,0.75)'

    @pytest.mark.parametrize('alpha', [0.0, 0.2, 0.35, 1.0])
    def test_alpha_passed_through(self, alpha):
        assert hex_to_rgba('#123456', alpha).endswith(f',{alpha})')


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  safe_date                                                                 ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class TestSafeDate:

    def test_normal_date(self):
        assert safe_date(2008, 6, 15) == pd.Timestamp('2008-06-15')

    def test_clamp_day_31_in_february(self):
        assert safe_date(2008, 2, 31) == pd.Timestamp('2008-02-29')  # 2008 is a leap year

    def test_clamp_day_31_in_non_leap_february(self):
        assert safe_date(2009, 2, 31) == pd.Timestamp('2009-02-28')

    def test_clamp_day_31_in_april(self):
        assert safe_date(2010, 4, 31) == pd.Timestamp('2010-04-30')

    def test_day_1_unchanged(self):
        assert safe_date(2009, 1, 1) == pd.Timestamp('2009-01-01')

    def test_dec_31(self):
        assert safe_date(2010, 12, 31) == pd.Timestamp('2010-12-31')

    @pytest.mark.parametrize('month', range(1, 13))
    def test_day_31_never_raises(self, month):
        """The whole point of safe_date: a 31 from a dropdown must never blow up."""

        assert isinstance(safe_date(2011, month, 31), pd.Timestamp)


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  get_auto_zoom                                                             ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class TestGetAutoZoom:

    def test_returns_float(self):
        assert isinstance(get_auto_zoom(-110, -95, 35, 45), float)

    def test_zero_lon_span_returns_fallback(self):
        assert get_auto_zoom(10, 10, 20, 40) == 8.5

    def test_zero_lat_span_returns_fallback(self):
        assert get_auto_zoom(-110, -95, 30, 30) == 8.5

    def test_larger_area_gives_smaller_zoom(self):
        z_small = get_auto_zoom(-101, -99, 39, 41)
        z_large = get_auto_zoom(-120, -80, 25, 55)
        assert z_small > z_large

    def test_zoom_is_reasonable(self):
        z = get_auto_zoom(-110, -95, 35, 45)
        assert 1.0 <= z <= 15.0

    def test_rounded_to_one_decimal(self):
        z = get_auto_zoom(-110, -95, 35, 45)
        assert z == round(z, 1)

    def test_wider_canvas_does_not_reduce_zoom(self):
        narrow = get_auto_zoom(-110, -95, 35, 45, map_width_px=800)
        wide = get_auto_zoom(-110, -95, 35, 45, map_width_px=1600)
        assert wide >= narrow

    def test_limiting_dimension_wins(self):
        """The zoom is the smaller of the longitude- and latitude-derived values."""

        import math
        min_lon, max_lon, min_lat, max_lat = -110, -95, 35, 45
        w, h = 1300, 550
        zoom_lon = math.log2(360 * w / (256 * (max_lon - min_lon)))
        zoom_lat = math.log2(180 * h / (256 * (max_lat - min_lat)))
        assert get_auto_zoom(min_lon, max_lon, min_lat, max_lat, w, h) \
            == round(min(zoom_lon, zoom_lat) - 0.5, 1)

    def test_half_step_margin_is_applied(self):
        """A 0.5 margin is subtracted so the extent is not flush to the edge."""

        import math
        min_lon, max_lon, min_lat, max_lat = -110, -95, 35, 45
        w, h = 1300, 550
        exact = min(math.log2(360 * w / (256 * (max_lon - min_lon))),
                    math.log2(180 * h / (256 * (max_lat - min_lat))))
        assert get_auto_zoom(min_lon, max_lon, min_lat, max_lat, w, h) < exact


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  rdp_keep_mask                                                             ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

def _square(n=None):
    """A closed unit square, optionally with n collinear points per edge."""

    corners = [[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]
    if n is None:
        return corners
    out = []
    for (x0, y0), (x1, y1) in zip(corners, corners[1:]):
        for i in range(n):
            t = i / n
            out.append([x0 + (x1 - x0) * t, y0 + (y1 - y0) * t])
    out.append(corners[-1])
    return out


class TestRdpKeepMask:

    def test_endpoints_always_kept(self):
        mask = rdp_keep_mask(np.array([[0., 0.], [1., 1.], [2., 2.]]), 0.1)
        assert mask[0] and mask[-1]

    def test_collinear_interior_points_dropped(self):
        line = np.array([[0., 0.], [1., 0.], [2., 0.], [3., 0.]])
        assert rdp_keep_mask(line, 0.1).sum() == 2

    def test_corner_above_tolerance_is_kept(self):
        pts = np.array([[0., 0.], [1., 1.], [2., 0.]])
        assert rdp_keep_mask(pts, 0.1).all()

    def test_corner_below_tolerance_is_dropped(self):
        pts = np.array([[0., 0.], [1., 0.001], [2., 0.]])
        assert rdp_keep_mask(pts, 0.1).sum() == 2

    def test_larger_tolerance_keeps_no_more_points(self):
        pts = np.array(_square(20), dtype=float)
        assert rdp_keep_mask(pts, 0.5).sum() <= rdp_keep_mask(pts, 0.001).sum()

    def test_square_reduces_to_its_corners(self):
        pts = np.array(_square(20), dtype=float)
        assert rdp_keep_mask(pts, 0.01).sum() == 5

    def test_coincident_endpoints_use_radial_distance(self):
        """A closed sub-path has a zero-length chord; the far point must survive."""

        pts = np.array([[0., 0.], [1., 0.], [0., 0.]])
        assert rdp_keep_mask(pts, 0.1).all()

    def test_empty_input(self):
        assert len(rdp_keep_mask(np.empty((0, 2)), 0.1)) == 0

    def test_long_ring_does_not_hit_the_recursion_limit(self):
        """The implementation is iterative precisely so this cannot fail."""

        t = np.linspace(0, 2 * np.pi, 60000)
        pts = np.column_stack([np.cos(t), np.sin(t)])
        assert rdp_keep_mask(pts, 1e-6).sum() > 2


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  simplify_ring                                                             ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class TestSimplifyRing:

    def test_square_keeps_five_points(self):
        assert len(simplify_ring(_square(20), 0.01)) == 5

    def test_result_is_closed(self):
        ring = simplify_ring(_square(20), 0.01)
        assert ring[0] == ring[-1]

    def test_coordinates_are_rounded(self):
        ring = simplify_ring([[0.123456789, 0.0], [1.0, 1.0], [2.0, 0.0],
                              [0.123456789, 0.0]], 0.01)
        assert ring[0] == [0.12346, 0.0]

    def test_speck_below_tolerance_collapses_to_none(self):
        tiny = [[0.0, 0.0], [0.001, 0.0], [0.001, 0.001], [0.0, 0.0]]
        assert simplify_ring(tiny, 0.1) is None

    def test_degenerate_ring_returns_none(self):
        assert simplify_ring([[0.0, 0.0], [1.0, 1.0]], 0.01) is None

    def test_unclosed_input_is_closed(self):
        ring = simplify_ring([[0., 0.], [1., 0.], [1., 1.], [0., 1.]], 0.01)
        assert ring[0] == ring[-1]


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  simplify_geojson                                                          ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

def _fc(*geometries):
    return {'type': 'FeatureCollection',
            'features': [{'type': 'Feature', 'properties': {'name': 'x'},
                          'geometry': g} for g in geometries]}


_POLY = {'type': 'Polygon', 'coordinates': [_square(20)]}


class TestSimplifyGeojson:

    def test_returns_a_feature_collection(self):
        assert simplify_geojson(_fc(_POLY), 0.01)['type'] == 'FeatureCollection'

    def test_polygon_survives(self):
        assert len(simplify_geojson(_fc(_POLY), 0.01)['features']) == 1

    def test_vertex_count_is_reduced(self):
        out = simplify_geojson(_fc(_POLY), 0.01)
        assert len(out['features'][0]['geometry']['coordinates'][0]) == 5

    def test_properties_are_dropped(self):
        assert simplify_geojson(_fc(_POLY), 0.01)['features'][0]['properties'] == {}

    def test_input_is_not_modified(self):
        src = _fc(_POLY)
        before = len(src['features'][0]['geometry']['coordinates'][0])
        simplify_geojson(src, 0.01)
        assert len(src['features'][0]['geometry']['coordinates'][0]) == before

    def test_multipolygon_is_flattened_into_one_feature_each(self):
        multi = {'type': 'MultiPolygon', 'coordinates': [[_square(20)], [_square(20)]]}
        assert len(simplify_geojson(_fc(multi), 0.01)['features']) == 2

    def test_output_is_all_polygons(self):
        multi = {'type': 'MultiPolygon', 'coordinates': [[_square(20)]]}
        out = simplify_geojson(_fc(_POLY, multi), 0.01)
        assert {f['geometry']['type'] for f in out['features']} == {'Polygon'}

    def test_non_polygon_geometry_is_skipped(self):
        point = {'type': 'Point', 'coordinates': [0.0, 0.0]}
        assert simplify_geojson(_fc(point), 0.01)['features'] == []

    def test_feature_with_only_collapsed_rings_is_dropped(self):
        tiny = {'type': 'Polygon',
                'coordinates': [[[0., 0.], [0.001, 0.], [0.001, 0.001], [0., 0.]]]}
        assert simplify_geojson(_fc(tiny), 0.1)['features'] == []

    def test_interior_rings_are_kept(self):
        hole = [[0.2, 0.2], [0.8, 0.2], [0.8, 0.8], [0.2, 0.8], [0.2, 0.2]]
        poly = {'type': 'Polygon', 'coordinates': [_square(20), hole]}
        out = simplify_geojson(_fc(poly), 0.01)
        assert len(out['features'][0]['geometry']['coordinates']) == 2

    def test_empty_collection(self):
        assert simplify_geojson({'type': 'FeatureCollection', 'features': []}) \
            == {'type': 'FeatureCollection', 'features': []}

    def test_crs_member_is_not_carried_over(self):
        """GeoJSON is WGS84 by definition; the member is deprecated."""

        src = _fc(_POLY)
        src['crs'] = {'type': 'name', 'properties': {'name': 'urn:ogc:def:crs:OGC:1.3:CRS84'}}
        assert 'crs' not in simplify_geojson(src, 0.01)
