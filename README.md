<p align="center">
  <img src="https://raw.githubusercontent.com/aquacropos/geoaquacrop_visualize/main/docs/_static/logo-mark.png"
       alt="" width="130">
</p>

<h1 align="center">geoaquacrop_visualize</h1>

<p align="center">Interactive Dash/Plotly viewer for gridded AquaCrop-OSPy simulations in the GeoAquaCrop toolchain.</p>

<p align="center">
  <a href="https://pypi.org/project/geoaquacrop-visualize/"><img src="https://img.shields.io/pypi/v/geoaquacrop-visualize" alt="PyPI"></a>
  <a href="https://pypi.org/project/geoaquacrop-visualize/"><img src="https://img.shields.io/pypi/pyversions/geoaquacrop-visualize" alt="Python"></a>
  <a href="https://geoaquacrop-visualize.readthedocs.io/en/latest/"><img src="https://img.shields.io/readthedocs/geoaquacrop-visualize" alt="Docs"></a>
  <a href="https://github.com/aquacropos/geoaquacrop_visualize/actions/workflows/tests.yml"><img src="https://github.com/aquacropos/geoaquacrop_visualize/actions/workflows/tests.yml/badge.svg" alt="Tests"></a>
  <a href="https://pepy.tech/projects/geoaquacrop-visualize"><img src="https://static.pepy.tech/personalized-badge/geoaquacrop-visualize?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads" alt="PyPI Downloads"></a>
  <a href="https://github.com/aquacropos/geoaquacrop_visualize/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-Apache%202.0-blue" alt="License"></a>
</p>

## Install

```bash
pip install geoaquacrop_visualize
```

Or install the whole toolchain in one go:

```bash
pip install geoaquacrop
```

Optional extras:

| Extra | Brings in | For |
|---|---|---|
| `geotiff` | rasterio | GeoTIFF export. Without it, that format is skipped and NetCDF and CSV still work. |
| `docs` | sphinx, furo | Building the documentation locally |
| `test` | pytest | Running the test suite |
| `dev` | all of the above | Contributing |

```bash
pip install "geoaquacrop_visualize[geotiff]"
```

Requires Python 3.11+, the simulation outputs produced by
[geoaquacrop_simulate](https://github.com/aquacropos/geoaquacrop_simulate), and the
harmonized inputs produced by
[geoaquacrop_preprocess](https://github.com/aquacropos/geoaquacrop_preprocess).

## Overview

**geoaquacrop_visualize** is an interactive viewer for gridded
[AquaCrop-OSPy](https://github.com/aquacropos/aquacrop) runs. Point it at a completed
run and it gives you a map of the region, a variable picker, and a click-through to
per-cell daily time series. It also shows the inputs that drove the run and exports
any selection as a gridded file. The app is a viewer, not a model: it reads results
and never runs AquaCrop itself.

It is the final stage of the GeoAquaCrop toolchain:

```
geoaquacrop_preprocess  ->  geoaquacrop_simulate  ->  geoaquacrop_visualize
(download & harmonize)      (simulate & correct)      (explore results)
```

| Feature | Description |
|---|---|
| Choropleth maps | 11 seasonal output variables (yield, production, irrigation, ET, water productivity) over the simulation grid, on an OpenFreeMap Positron basemap with the region outline on top |
| Daily time series | 13 daily variables (water fluxes, soil water, crop development) for any cell, read from the simulation's daily tables |
| Model inputs | Climate forcing (4 variables), crop calendar and SPAM physical crop areas on the same grid as the outputs |
| Spatial selection | Click a cell for its time series; lasso or box-select many cells to highlight them and scope an export to that area |
| Season handling | One season at a time, or all years aggregated by mean or sum |
| Gridded export | Any set of cells, variables and dates to NetCDF, GeoTIFF or CSV |

All data loads once at startup, so interaction is instant afterwards.

## Quick start

```python
import geoaquacrop_visualize as visualize

visualize.run(
    outputs='/path/to/geoaquacrop_simulate/outputs',
    processed='/path/to/geoaquacrop_preprocess/processed',
    region='/path/to/region.geojson',
    port=8050,
)
```

Then open <http://localhost:8050>.

`root` fills all three paths at once when they sit under one workspace folder (see
[Input files](#input-files)).

The same call through the unified toolchain façade:

```python
import geoaquacrop as gac

gac.visualize.run(root='/path/to/workspace')
```

From the command line:

```bash
geoaquacrop_visualize --root /path/to/workspace
```

Run `geoaquacrop_visualize --help` for every option, including `--port`, `--debug`
and `--version`.

Startup checks that the region outline, both result pickles and the `processed/`
folder exist, loads every dataset, precomputes the
aggregations, and prints the derived map zoom and region boundary statistics. Expect a
few seconds, depending on the size of your run.

The datasets are held in module-level state, so one process serves one workspace.
Calling `build_app()` again with a different `root` returns the app built from the
first. Use a separate process per workspace.

To serve the app behind a WSGI server such as gunicorn, build it without starting a
server:

```python
from geoaquacrop_visualize import build_app

server = build_app().server
```

## Input files

By default the app reads from the folder you launch it from, or from the workspace
given by `--root` or `$GEOAQUACROP_ROOT`:

```
<workspace>/
├── outputs/
│   ├── summary_results_<timestamp>.pkl
│   └── daily_results_<timestamp>.pkl
├── processed/
│   ├── MaxTemp*.nc  MinTemp*.nc  Precipitation*.nc  ReferenceET*.nc
│   ├── cropcalendar.nc
│   └── spam*_physical_area.nc
└── region.geojson
```

| File | Produced by | Contents |
|---|---|---|
| `summary_results_<timestamp>.pkl` | geoaquacrop_simulate | Seasonal results per cell |
| `daily_results_<timestamp>.pkl` | geoaquacrop_simulate | Daily water-balance and crop-growth tables per cell |
| `MaxTemp*.nc`, `MinTemp*.nc`, `Precipitation*.nc`, `ReferenceET*.nc` | geoaquacrop_preprocess | Daily climate forcing |
| `cropcalendar.nc` | geoaquacrop_preprocess | Planting DOY and growing season length |
| `spam*_physical_area.nc` | geoaquacrop_preprocess | Crop physical area per type and irrigation mode |
| `region.geojson` | user | Region outline drawn on the map, usually the domain polygon given to geoaquacrop_preprocess |

If your data lives elsewhere, pass each location as an option (`--outputs`,
`--processed`, `--region`, `--exports`), as the matching keyword argument of `run()`,
or as an environment variable:

```bash
export GEOAQUACROP_OUTPUTS=/path/to/geoaquacrop_simulate/outputs
export GEOAQUACROP_PROCESSED=/path/to/geoaquacrop_preprocess/processed
export GEOAQUACROP_REGION=/path/to/domain.geojson
```

If `outputs/` holds several runs, the newest `summary_results_*.pkl` and
`daily_results_*.pkl` (by filename) are loaded. To view another run, point
`GEOAQUACROP_OUTPUTS` at a folder that holds only that run. Each geoaquacrop_simulate
run covers one crop and one irrigation type, so the crop list in the app usually has
a single entry.

The app reads yields from the summary pickle only. With the `scale` correction in
geoaquacrop_simulate, the scaled yields go to `yield_scaled.nc`, which the app does
not read, so the maps show unscaled yields. With `calibrate`, the run itself uses the
calibrated parameter, so the maps already reflect it.

No data is bundled with the package, and none needs to be copied into it.

## Using the app

The window has a control sidebar on the left and a map canvas on the right. Two tabs
at the top of the sidebar switch the view.

### Simulation Outputs tab

1. Choose a **crop**, an **irrigation type** and a **season**: a single harvest year,
   or *All years*.
2. With *All years*, an **Aggregation** toggle appears (*Mean* or *Sum*). The default
   is *Mean*.
3. Pick a **map variable** from the *Yield & Production*, *Water Balance* or
   *Water Productivity* groups. The map recolors immediately.
4. **Click a cell** to open its daily time series below the map. Choose the daily
   variable from the *Water Fluxes*, *Soil Water* or *Crop Development* groups. For a
   single season, the series covers that calendar year.
5. **Click two points on the time series** to mark a window. The app shades it, draws
   the mean as a dashed line, and reports the mean ± standard deviation. A third click
   clears it.
6. **Lasso or box-select** cells with the Plotly toolbar at the top right of the map to
   highlight them. The export dialog shows the count and can then be limited to that
   selection.

### Inputs tab

Shows the data that drove the simulation on the same grid: the chosen climate
variable and SPAM physical crop areas for the selected crop. A line above the map
gives the crop calendar for the selected crop and irrigation type (planting date,
season length, approximate harvest). Clicking a cell opens its climate time series.

Pan and zoom persist as you change variables. Hovering a cell shows its coordinates
and the current value.

## Exported files

**⬇ Export Data…** at the bottom of the sidebar opens a dialog with four choices:

| Choice | Options |
|---|---|
| Variables | Any of the 13 daily variables, grouped as in the sidebar |
| Period | The whole simulation, or an explicit start and end date |
| Cells | The whole area, or the current map selection |
| Format | NetCDF (`.nc`), GeoTIFF (`.tif`), CSV (`.csv`), in any combination |

Each variable is written to `<workspace>/outputs/exports/` (override with `--exports`
or `$GEOAQUACROP_EXPORTS`), as a time × y × x grid for NetCDF and GeoTIFF and as one
row per cell and date for CSV. The dialog lists the files it wrote. GeoTIFF needs the `geotiff` extra; without it, that format is skipped with a
note and the others are still written.

## Configuration reference

All settings live in
[`src/geoaquacrop_visualize/config.py`](https://github.com/aquacropos/geoaquacrop_visualize/blob/main/src/geoaquacrop_visualize/config.py).

| Parameter | Default | Description |
|---|---|---|
| `ROOT` | `$GEOAQUACROP_ROOT` or working directory | Workspace root; the paths below default to locations under it |
| `OUTPUTS_DIR` | `$GEOAQUACROP_OUTPUTS` or `outputs` | Folder holding the simulation result pickles |
| `PROCESSED_DIR` | `$GEOAQUACROP_PROCESSED` or `processed` | Climate, crop calendar and SPAM grids |
| `GEOJSON_PATH` | `$GEOAQUACROP_REGION` or `region.geojson` | Region outline |
| `CELL_RES` | `$GEOAQUACROP_CELL_RES` or `0.05` | Grid cell size in degrees; must match the preprocessing grid |
| `SUMMARY_PKL`, `DAILY_PKL` | newest match in `OUTPUTS_DIR` | Simulation run to display |
| `EXPORT_DIR` | `$GEOAQUACROP_EXPORTS` or `outputs/exports` | Where exports are written |
| `PORT` | `$GEOAQUACROP_PORT` or `8050` | Port the app serves on |
| `MAP_HEIGHT`, `TS_HEIGHT` | `550`, `400` | Canvas heights in pixels |
| `BOUNDARY_SIMPLIFY_EPS` | `0.004` | Outline simplification tolerance in degrees (~400 m) |
| `MAP_VARIABLES` | 11 entries | Map variable catalog: label, color scale, default aggregation |
| `DAILY_VARIABLES` | 13 entries | Daily variable catalog: label, source table, line color |
| `CLIMATE_VARIABLES` | 4 entries | Climate variable catalog |

To add a variable, add an entry to the relevant catalog. For map and daily variables,
also list the key in its group in `styles.py`, which places it in the sidebar and the
export dialog.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `Cannot start: ... required input(s) not found` | The message lists every missing input and the path tried. Launch from the workspace folder, pass `--root`, or set each location with `--outputs`, `--processed` and `--region`. |
| The wrong run is displayed | The newest pickles in `GEOAQUACROP_OUTPUTS` are loaded. Check that both come from the same run, or point to a folder holding only the run you want. |
| No region outline on the map | Check the `Region boundary: …` line printed at startup. If it is missing or reports zero polygons, inspect the source GeoJSON. |
| `GeoTIFF skipped` in the export status | Install the extra: `pip install "geoaquacrop_visualize[geotiff]"`. |
| Blank map, working sidebar | Basemap tiles come from OpenFreeMap's public server and need network access. The data layers render regardless. |

## Documentation

Full documentation: https://geoaquacrop-visualize.readthedocs.io/en/latest/

## Development

To work on the package itself:

```bash
git clone https://github.com/aquacropos/geoaquacrop_visualize
cd geoaquacrop_visualize
conda create -n geoaquacrop python=3.11
conda activate geoaquacrop
python -m pip install -e ".[dev]"
```

Run the tests:

```bash
python -m pytest -q
```

No data files are needed for the tests. The suite also enforces the package layout:
no module exceeds 500 lines, the import graph stays acyclic, callbacks never import
each other, and only `data.py` opens the pickles and NetCDF files.

Build the documentation locally:

```bash
sphinx-build -b html docs docs/_build/html
```

Do not execute module files directly. A module run as a script has no package context
and its relative imports fail.

## License

Apache 2.0. See [LICENSE](https://github.com/aquacropos/geoaquacrop_visualize/blob/main/LICENSE).

## Data attributions

geoaquacrop_visualize does not contain any of the data it displays. Simulation
results and inputs come from your own runs of geoaquacrop_simulate and
geoaquacrop_preprocess; see the
[geoaquacrop_preprocess data attributions](https://github.com/aquacropos/geoaquacrop_preprocess#data-attributions)
for how to credit the underlying climate, soil, crop calendar and crop area datasets.

### Basemap: OpenFreeMap

The basemap uses the Positron style from [OpenFreeMap](https://openfreemap.org).
Map data: [© OpenMapTiles](https://www.openmaptiles.org/), data from
[OpenStreetMap](https://www.openstreetmap.org/copyright).
