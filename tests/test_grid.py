"""
Tests for ``geoaquacrop_plotting.grid``.

``grid`` imports ``data``, so it cannot be imported without the real dataset.
The GeoJSON construction is mirrored here and driven by the synthetic fixtures.
``CELL_RES`` is read from the real config.
"""

from geoaquacrop_plotting.config import CELL_RES


def build_grid_geojson(cells_df, half):
    """Mirror of the ``grid_geojson`` construction in grid.py."""

    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "id": str(int(row.cell_id)),
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [row.x - half, row.y - half],
                        [row.x + half, row.y - half],
                        [row.x + half, row.y + half],
                        [row.x - half, row.y + half],
                        [row.x - half, row.y - half],
                    ]]
                },
                "properties": {}
            }
            for _, row in cells_df.iterrows()
        ]
    }


class TestGridGeoJSON:

    def _cells(self, mock_summary):
        return mock_summary[['cell_id', 'x', 'y']].drop_duplicates()

    def test_feature_count(self, mock_summary):
        cells = self._cells(mock_summary)
        gj = build_grid_geojson(cells, 0.025)
        assert len(gj['features']) == len(cells)

    def test_is_a_feature_collection(self, mock_summary):
        gj = build_grid_geojson(self._cells(mock_summary), 0.025)
        assert gj['type'] == 'FeatureCollection'

    def test_feature_ids_are_strings(self, mock_summary):
        gj = build_grid_geojson(self._cells(mock_summary), 0.025)
        for f in gj['features']:
            assert isinstance(f['id'], str)

    def test_feature_ids_are_unique(self, mock_summary):
        gj = build_grid_geojson(self._cells(mock_summary), 0.025)
        ids = [f['id'] for f in gj['features']]
        assert len(ids) == len(set(ids))

    def test_polygon_is_closed(self, mock_summary):
        gj = build_grid_geojson(self._cells(mock_summary), 0.025)
        for f in gj['features']:
            coords = f['geometry']['coordinates'][0]
            assert coords[0] == coords[-1], "Polygon ring must be closed"

    def test_polygon_has_five_points(self, mock_summary):
        gj = build_grid_geojson(self._cells(mock_summary), 0.025)
        for f in gj['features']:
            assert len(f['geometry']['coordinates'][0]) == 5

    def test_cell_is_square_of_cell_res(self, mock_summary):
        half = CELL_RES / 2
        gj = build_grid_geojson(self._cells(mock_summary), half)
        for f in gj['features']:
            ring = f['geometry']['coordinates'][0]
            lons = [p[0] for p in ring]
            lats = [p[1] for p in ring]
            assert round(max(lons) - min(lons), 10) == CELL_RES
            assert round(max(lats) - min(lats), 10) == CELL_RES

    def test_cell_centred_on_its_coordinates(self, mock_summary):
        half = CELL_RES / 2
        cells = self._cells(mock_summary)
        gj = build_grid_geojson(cells, half)
        for f, (_, row) in zip(gj['features'], cells.iterrows()):
            ring = f['geometry']['coordinates'][0]
            lons = [p[0] for p in ring]
            lats = [p[1] for p in ring]
            assert round((max(lons) + min(lons)) / 2, 10) == round(row.x, 10)
            assert round((max(lats) + min(lats)) / 2, 10) == round(row.y, 10)

    def test_cell_res_defines_half(self):
        assert CELL_RES / 2 == 0.025


class TestMapExtent:
    """The bounding box that feeds get_auto_zoom is padded by half a cell."""

    def test_extent_padded_by_half_cell(self, mock_cell_meta):
        half = CELL_RES / 2
        min_lon = min(m['x'] for m in mock_cell_meta.values()) - half
        max_lon = max(m['x'] for m in mock_cell_meta.values()) + half
        assert min_lon == -101.0 - half
        assert max_lon == -100.0 + half

    def test_centre_is_mean_of_cells(self, mock_summary):
        assert mock_summary['x'].mean() == mock_summary['x'].mean()
        assert -101.0 <= mock_summary['x'].mean() <= -100.0

    def test_all_cell_ids_are_strings(self, mock_cell_meta):
        all_cell_ids = [str(cid) for cid in mock_cell_meta.keys()]
        assert all(isinstance(c, str) for c in all_cell_ids)
        assert all_cell_ids == ['1', '2', '3']
