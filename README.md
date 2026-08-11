# GeoAquaCrop Visualizer

An interactive web-based visualisation toolkit for gridded [AquaCrop](https://www.fao.org/aquacrop/en/) simulations. Built with Python, Dash, and Plotly, it provides spatial and temporal exploration of simulation outputs and climate inputs across large multi-cell grids.


---

## Features

### Simulation Outputs
- Spatial map of yield, water balance, and water productivity variables
- Per-season and multi-year aggregated views (mean or sum)
- Lasso and box selection of cells for spatial subsets
- Daily time series for any selected cell: water fluxes, soil water, crop development
- Interactive mean ± std window tool on time series

### Climate Inputs
- Spatial map of max/min temperature, precipitation, and reference ET
- Per-year or full-period averages
- Daily climate time series with planting date overlays from crop calendar
- SPAM crop area overlay for rainfed and irrigated extents

### Export
- Export daily gridded output to NetCDF, GeoTIFF, or CSV
- Flexible date range and spatial subset (whole area or lasso selection)

---

## Requirements

| Package | Purpose |
|---|---|
| Python 3.10+ | Runtime |
| pandas | Data manipulation |
| numpy | Array operations |
| xarray | NetCDF climate files |
| plotly | Interactive figures |
| dash | Web application framework |
| dash-bootstrap-components | Sidebar layout |
| rasterio | GeoTIFF export (optional) |

Install all dependencies via conda:

```bash
conda env create -f environment.yml
conda activate geoaquacrop-visualizer
```

---

## Installation

```bash
git clone https://github.com/aquacropos/geoaquacrop-visualizer.git
conda env create -f environment.yml
conda activate geoaquacrop-visualizer
```

---

## Configuration

Edit the `USER CONFIGURATION` block at the top of `geoaquacrop_plots.py`:

```python
SUMMARY_PKL   = '../outputs/summary_results_*.pkl'
DAILY_PKL     = '../outputs/daily_results_*.pkl'
GEOJSON_PATH  = '../inputdata/*.geojson'
PROCESSED_DIR = '../processed'
EXPORT_DIR    = '../outputs/exports'
CELL_RES      = 0.05   # grid resolution in degrees — must match preprocessing
PORT          = 8050
MAP_HEIGHT    = 550
TS_HEIGHT     = 400
```

All paths are resolved relative to the script location, so the app can be launched from any working directory.

---

## Usage

```bash
/opt/anaconda3/envs/geoaquacrop-visualizer/bin/python geoaquacrop_plots.py
```

Then open [http://localhost:8050](http://localhost:8050) in your browser.

The app will print the auto-computed map zoom level on startup:

```
Auto zoom: 4.5
Dash is running on http://127.0.0.1:8050/
```

---

## Input Data Structure

The app expects the following preprocessed files in `PROCESSED_DIR`:

| File | Description |
|---|---|
| `MaxTemp<YYYY><YYYY>.nc` | Daily maximum temperature grid |
| `MinTemp<YYYY><YYYY>.nc` | Daily minimum temperature grid |
| `Precipitation<YYYY><YYYY>.nc` | Daily precipitation grid |
| `ReferenceET<YYYY><YYYY>.nc` | Daily reference ET grid |
| `cropcalendar.nc` | Planting DOY and growing season length per crop |
| `spam*_physical_area.nc` | SPAM crop physical area (optional) |

Year range in filenames is auto-detected from the simulation period (e.g. `MaxTemp20082010.nc`).

Simulation outputs are loaded from two pickle files:

- `summary_results_*.pkl` — seasonal aggregated results per cell
- `daily_results_*.pkl` — daily water flux and crop growth tables per cell

---

## Map Variables

| Group | Variables |
|---|---|
| Yield & Production | Dry yield, fresh yield, yield potential, production (tonnes) |
| Water Balance | Seasonal irrigation, precipitation, ET, transpiration, total water input |
| Water Productivity | WP-ET (kg/m³), rainfall use efficiency (kg/m³) |

## Daily Variables

| Group | Variables |
|---|---|
| Water Fluxes | Soil evaporation, potential evaporation, transpiration, potential transpiration, infiltration, runoff, deep percolation |
| Soil Water | Water in root zone |
| Crop Development | Biomass, canopy cover, cumulative GDD, root depth, dry yield |

---

## Running Tests

Unit tests cover configuration constants, helper functions, data structures, figure builder logic, callback state machines, and export routines. They run without any data files using synthetic fixtures.

```bash
/opt/anaconda3/envs/geoaquacrop-visualizer/bin/pytest test.py -v
```

Tests are organised into 14 classes (~120 tests total). They are designed to run in CI on every commit without requiring the actual simulation data.

---

## Project Structure

```
geoaquacrop-visualizer/
├── aquacropgrid-plots.py     # Main application
├── testd.py                  # Automated test suite
├── README.md                 # This file
├── environment.yml           # Conda environment
├── docs		      # Documentation
└── ...
```

---
