"""
Shared pytest configuration and fixtures for the GeoAquaCrop Visualizer suite.

The suite runs WITHOUT the real simulation data. Three things make that work:

1. A stub workspace. ``geoaquacrop_plotting.config`` locates the sibling
   ``geoaquacrop-preproc`` / ``geoaquacrop-simulate`` trees at import time and
   raises if it cannot find them. Pointing ``GEOAQUACROP_ROOT`` at an empty
   stub directory satisfies that check without reading a data file.

2. A stub parent package. Importing ``geoaquacrop_plotting`` normally runs its
   ``__init__``, which builds the entire app — loading the pickles, assembling
   the layout, registering the callbacks. Registering a bare module object
   under that name first, carrying only ``__path__``, lets the data-free
   submodules (``config``, ``utils``, ``styles``, ``app_shell``) be imported
   and tested for real while ``__init__`` never runs.

3. Synthetic fixtures. The remaining modules (``data`` and everything that
   imports it: ``grid``, ``aggregates``, ``queries``, ``figures_*``,
   ``export``, ``layout*``, ``callbacks_*``) genuinely cannot be imported
   without the dataset, so their tests mirror the same logic and drive it with
   the fixtures below. Each test module's docstring says which case it is.
"""

import os
import pathlib
import sys
import tempfile
import types

from _paths import IMPORT_ROOT, PKG_DIR

# ── 1. Stub workspace: set before geoaquacrop_plotting.config is imported ─────
_STUB_WORKSPACE = tempfile.mkdtemp(prefix='geoaquacrop-test-workspace-')
pathlib.Path(_STUB_WORKSPACE, 'geoaquacrop-preproc').mkdir(exist_ok=True)
pathlib.Path(_STUB_WORKSPACE, 'geoaquacrop-simulate').mkdir(exist_ok=True)
os.environ['GEOAQUACROP_ROOT'] = _STUB_WORKSPACE

# ── 2. Stub parent package, so submodule imports skip the app-building init ───
if str(IMPORT_ROOT) not in sys.path:
    sys.path.insert(0, str(IMPORT_ROOT))

if 'geoaquacrop_plotting' not in sys.modules:
    _pkg = types.ModuleType('geoaquacrop_plotting')
    _pkg.__path__ = [str(PKG_DIR)]
    _pkg.__doc__ = ('Test stub: the real __init__ builds the whole Dash app, '
                    'which needs the dataset. See tests/conftest.py.')
    sys.modules['geoaquacrop_plotting'] = _pkg

import numpy as np                                          # noqa: E402
import pandas as pd                                         # noqa: E402
import pytest                                               # noqa: E402


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  FIXTURES — synthetic data that mirrors real data structures               ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

@pytest.fixture
def mock_cell_meta():
    """Three cells, mirroring the structure of ``data.cell_meta``."""

    return {
        1: {'x': -100.0, 'y': 40.0, 'crop': 'maize', 'irrigation': 'rainfed',  'list_idx': 0},
        2: {'x': -100.5, 'y': 40.5, 'crop': 'maize', 'irrigation': 'rainfed',  'list_idx': 1},
        3: {'x': -101.0, 'y': 41.0, 'crop': 'maize', 'irrigation': 'irrigated','list_idx': 2},
    }


@pytest.fixture
def mock_summary():
    """Three cells × three seasons, mirroring the columns of ``data.summary``."""

    rows = []
    for cell_id, x, y, irr in [(1, -100.0, 40.0, 'rainfed'),
                                 (2, -100.5, 40.5, 'rainfed'),
                                 (3, -101.0, 41.0, 'irrigated')]:
        for yr in [2008, 2009, 2010]:
            rows.append({
                'cell_id': cell_id, 'x': x, 'y': y,
                'crop': 'maize', 'irrigation': irr,
                'harvest_year': yr,
                'season_label': str(yr),
                'crop_irr': f'maize | {irr}',
                'Dry yield (tonne/ha)': np.random.uniform(3, 8),
                'Fresh yield (tonne/ha)': np.random.uniform(10, 20),
                'Yield potential (tonne/ha)': np.random.uniform(8, 12),
                'production_tonnes': np.random.uniform(100, 500),
                'Seasonal irrigation (mm)': 0.0 if irr == 'rainfed' else np.random.uniform(100, 300),
                'seasonal_precip_mm': np.random.uniform(200, 600),
                'seasonal_et_mm': np.random.uniform(200, 500),
                'seasonal_transpiration_mm': np.random.uniform(150, 400),
                'total_water_input_mm': np.random.uniform(300, 700),
                'wp_et_kg_per_m3': np.random.uniform(0.5, 2.0),
                'rainfall_use_efficiency_kg_per_m3': np.random.uniform(0.3, 1.5),
            })
    return pd.DataFrame(rows)


@pytest.fixture
def mock_daily_wf():
    """Daily water-flux table, mirroring ``daily_raw[i]['water_flux']``."""

    n = 365 * 3
    df = pd.DataFrame({
        'Es':      np.random.uniform(0, 3, n),
        'EsPot':   np.random.uniform(0, 5, n),
        'Tr':      np.random.uniform(0, 4, n),
        'TrPot':   np.random.uniform(0, 6, n),
        'Infl':    np.random.uniform(0, 10, n),
        'Runoff':  np.random.uniform(0, 2, n),
        'DeepPerc':np.random.uniform(0, 1, n),
        'Wr':      np.random.uniform(50, 200, n),
        'season_counter': ([-1.0] * 60 + [1.0] * (365 - 60)) * 3,
    })
    return df


@pytest.fixture
def mock_daily_cg():
    """Daily crop-growth table, mirroring ``daily_raw[i]['crop_growth']``."""

    n = 365 * 3
    return pd.DataFrame({
        'biomass':      np.random.uniform(0, 15, n),
        'canopy_cover': np.random.uniform(0, 1, n),
        'gdd_cum':      np.cumsum(np.random.uniform(5, 15, n)),
        'z_root':       np.random.uniform(0.1, 0.6, n),
        'DryYield':     np.random.uniform(0, 8, n),
    })


@pytest.fixture
def date_index_3y():
    """A three-year daily index, as ``data.date_index`` would be."""

    return pd.date_range('2008-01-01', '2010-12-31', freq='D')


@pytest.fixture
def ts_click_reset():
    """The neutral click state used by the mean ± std window tool."""

    return {'count': 0, 'start': None, 'end': None}
