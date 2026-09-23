"""Cell grid geometry: the choropleth GeoJSON, map centre, and auto zoom."""

from .config import CELL_RES
from .utils import get_auto_zoom
from .data import summary, cell_meta

#: Half a cell width in degrees — the offset from a cell centre to its edge.
half  = CELL_RES / 2

#: The distinct ``(cell_id, x, y)`` rows the cell polygons are built from.
cells = summary[['cell_id', 'x', 'y']].drop_duplicates()

#: A FeatureCollection with one square Polygon per cell, its ``id`` set to the
#: cell id as a string. Every choropleth trace addresses cells through these
#: ids rather than shipping geometry per update.
grid_geojson = {
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
        for _, row in cells.iterrows()
    ]
}
#: Every cell id as a string, in ``cell_meta`` order — the ``locations`` array
#: of the background choropleth trace.
all_cell_ids = [str(cid) for cid in cell_meta.keys()]

#: Latitude the maps are centred on -- the mean of every cell centre.
center_lat   = summary['y'].mean()

#: Longitude the maps are centred on -- the mean of every cell centre.
center_lon   = summary['x'].mean()

min_lon  = min(m['x'] for m in cell_meta.values()) - half
max_lon  = max(m['x'] for m in cell_meta.values()) + half
min_lat  = min(m['y'] for m in cell_meta.values()) - half
max_lat  = max(m['y'] for m in cell_meta.values()) + half
#: Initial map zoom, derived from the grid's bounding box so the whole region
#: fits the canvas. Printed at startup.
MAP_ZOOM = get_auto_zoom(min_lon, max_lon, min_lat, max_lat)
print(f"Auto zoom: {MAP_ZOOM}")
