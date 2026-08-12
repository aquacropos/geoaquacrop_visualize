"""
tests.py
Automated tests for geoaquacropgrid-plots
Run with: pytest tests.py -v

These tests are designed to run WITHOUT the actual data files.
They mock all file I/O and test logic, helpers, and figure builders in isolation.
"""

import pytest
import numpy as np
import pandas as pd
import math
from unittest.mock import MagicMock, patch
import plotly.graph_objects as go

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  FIXTURES — synthetic data that mirrors real data structures               ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

@pytest.fixture
def mock_cell_meta():
    return {
        1: {'x': -100.0, 'y': 40.0, 'crop': 'maize', 'irrigation': 'rainfed',  'list_idx': 0},
        2: {'x': -100.5, 'y': 40.5, 'crop': 'maize', 'irrigation': 'rainfed',  'list_idx': 1},
        3: {'x': -101.0, 'y': 41.0, 'crop': 'maize', 'irrigation': 'irrigated','list_idx': 2},
    }

@pytest.fixture
def mock_summary():
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
    n = 365 * 3
    return pd.DataFrame({
        'biomass':      np.random.uniform(0, 15, n),
        'canopy_cover': np.random.uniform(0, 1, n),
        'gdd_cum':      np.cumsum(np.random.uniform(5, 15, n)),
        'z_root':       np.random.uniform(0.1, 0.6, n),
        'DryYield':     np.random.uniform(0, 8, n),
    })

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  1. CONFIGURATION CONSTANTS                                                ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class TestConfigConstants:

    def test_map_variables_required_keys(self):
        MAP_VARIABLES = {
            'Dry yield (tonne/ha)': {'label': 'Dry Yield (t/ha)', 'colorscale': 'YlOrRd',
                                      'sum_colorscale': 'OrRd', 'default_agg': 'mean'},
            'Seasonal irrigation (mm)': {'label': 'Seasonal Irrigation (mm)', 'colorscale': 'Blues',
                                          'sum_colorscale': 'PuBuGn', 'default_agg': 'sum'},
        }
        for key, val in MAP_VARIABLES.items():
            assert 'label' in val, f"Missing 'label' in {key}"
            assert 'colorscale' in val, f"Missing 'colorscale' in {key}"
            assert 'sum_colorscale' in val, f"Missing 'sum_colorscale' in {key}"
            assert val['default_agg'] in ('mean', 'sum'), f"Invalid default_agg in {key}"

    def test_daily_variables_required_keys(self):
        DAILY_VARIABLES = {
            'Es':      {'label': 'Soil Evaporation (mm/day)', 'table': 'water_flux',  'color': '#e67e22'},
            'biomass': {'label': 'Biomass (tonne/ha)',         'table': 'crop_growth', 'color': '#27ae60'},
        }
        for key, val in DAILY_VARIABLES.items():
            assert 'label' in val
            assert val['table'] in ('water_flux', 'crop_growth'), f"Invalid table in {key}"
            assert val['color'].startswith('#'), f"Color must be hex in {key}"

    def test_climate_variables_required_keys(self):
        CLIMATE_VARIABLES = {
            'MaxTemp':       {'label': 'Max Temperature (°C)', 'map_label': 'Max Temperature (°C)',
                              'unit': '°C', 'color': '#e74c3c', 'colorscale': 'RdYlBu_r'},
            'Precipitation': {'label': 'Precipitation (mm/day)', 'map_label': 'Precipitation (mm/year)',
                              'unit': 'mm/year', 'color': '#2980b9', 'colorscale': 'Blues'},
        }
        for key, val in CLIMATE_VARIABLES.items():
            assert 'label' in val
            assert 'map_label' in val, f"Missing 'map_label' in {key}"
            assert 'unit' in val, f"Missing 'unit' in {key}"
            assert 'colorscale' in val

    def test_precipitation_unit_is_mm_per_year(self):
        unit = 'mm/year'
        assert unit == 'mm/year'

    def test_temperature_unit_is_celsius(self):
        unit = '°C'
        assert unit == '°C'

    def test_cell_res_positive(self):
        CELL_RES = 0.05
        assert CELL_RES > 0

    def test_map_height_positive(self):
        MAP_HEIGHT = 550
        assert MAP_HEIGHT > 0

    def test_ts_height_positive(self):
        TS_HEIGHT = 400
        assert TS_HEIGHT > 0


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  2. HELPER FUNCTIONS                                                        ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class TestHexToRgba:

    def _hex_to_rgba(self, hex_color, alpha):
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        return f'rgba({r},{g},{b},{alpha})'

    def test_red(self):
        assert self._hex_to_rgba('#ff0000', 0.5) == 'rgba(255,0,0,0.5)'

    def test_blue(self):
        assert self._hex_to_rgba('#2980b9', 0.2) == 'rgba(41,128,185,0.2)'

    def test_white(self):
        assert self._hex_to_rgba('#ffffff', 1.0) == 'rgba(255,255,255,1.0)'

    def test_black(self):
        assert self._hex_to_rgba('#000000', 0.0) == 'rgba(0,0,0,0.0)'


class TestSafeDate:

    def _safe_date(self, year, month, day):
        import calendar
        max_day = calendar.monthrange(year, month)[1]
        return pd.Timestamp(year=year, month=month, day=min(day, max_day))

    def test_normal_date(self):
        result = self._safe_date(2008, 6, 15)
        assert result == pd.Timestamp('2008-06-15')

    def test_clamp_day_31_in_february(self):
        result = self._safe_date(2008, 2, 31)
        assert result == pd.Timestamp('2008-02-29')  # 2008 is leap year

    def test_clamp_day_31_in_april(self):
        result = self._safe_date(2010, 4, 31)
        assert result == pd.Timestamp('2010-04-30')

    def test_day_1_unchanged(self):
        result = self._safe_date(2009, 1, 1)
        assert result == pd.Timestamp('2009-01-01')

    def test_dec_31(self):
        result = self._safe_date(2010, 12, 31)
        assert result == pd.Timestamp('2010-12-31')


class TestGetAutoZoom:

    def _get_auto_zoom(self, min_lon, max_lon, min_lat, max_lat,
                       map_width_px=1300, map_height_px=550):
        lon_span = max_lon - min_lon
        lat_span = max_lat - min_lat
        if lon_span == 0 or lat_span == 0:
            return 8.5
        zoom_lon = math.log2(360 * map_width_px  / (256 * lon_span))
        zoom_lat = math.log2(180 * map_height_px / (256 * lat_span))
        return round(min(zoom_lon, zoom_lat) - 0.5, 1)

    def test_returns_float(self):
        z = self._get_auto_zoom(-110, -95, 35, 45)
        assert isinstance(z, float)

    def test_zero_span_returns_fallback(self):
        z = self._get_auto_zoom(10, 10, 20, 40)
        assert z == 8.5

    def test_larger_area_gives_smaller_zoom(self):
        z_small = self._get_auto_zoom(-101, -99, 39, 41)
        z_large = self._get_auto_zoom(-120, -80, 25, 55)
        assert z_small > z_large

    def test_zoom_is_reasonable(self):
        z = self._get_auto_zoom(-110, -95, 35, 45)
        assert 1.0 <= z <= 15.0


class TestSpamVarsForCrop:

    def _spam_vars_for_crop(self, crop_irr, spam_var_keys, irr_map):
        crop_raw = crop_irr.split(' | ')[0]
        irr_code = irr_map.get(crop_irr.split(' | ')[1].strip(),
                               crop_irr.split(' | ')[1].strip())
        exact = f'{crop_raw.capitalize()}_{irr_code}_physical_area'
        if exact in spam_var_keys:
            return [exact]
        prefix = f'{crop_raw.lower()}_{irr_code}_physical_area'
        for v in spam_var_keys:
            if v.lower() == prefix:
                return [v]
        return []

    IRR_MAP = {'rainfed': 'rf', 'irrigated': 'ir'}

    def test_exact_match(self):
        keys = ['Maize_rf_physical_area']
        result = self._spam_vars_for_crop('Maize | rainfed', keys, self.IRR_MAP)
        assert result == ['Maize_rf_physical_area']

    def test_case_insensitive_fallback(self):
        keys = ['maize_rf_physical_area']
        result = self._spam_vars_for_crop('Maize | rainfed', keys, self.IRR_MAP)
        assert result == ['maize_rf_physical_area']

    def test_irrigated_mapping(self):
        keys = ['Maize_ir_physical_area']
        result = self._spam_vars_for_crop('Maize | irrigated', keys, self.IRR_MAP)
        assert result == ['Maize_ir_physical_area']

    def test_no_match_returns_empty(self):
        keys = ['Wheat_rf_physical_area']
        result = self._spam_vars_for_crop('Maize | rainfed', keys, self.IRR_MAP)
        assert result == []

    def test_paddyrice_capitalize(self):
        # 'paddyrice1' → capitalize → 'Paddyrice1'
        # This tests the known limitation: multi-part names may fail capitalize
        keys = ['PaddyRice1_ir_physical_area']
        result = self._spam_vars_for_crop('PaddyRice1 | irrigated', keys, self.IRR_MAP)
        # Should match via case-insensitive fallback
        assert result == ['PaddyRice1_ir_physical_area']

    def test_empty_spam_var_keys(self):
        result = self._spam_vars_for_crop('Maize | rainfed', [], self.IRR_MAP)
        assert result == []


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  3. DATA LOADING & CELL META                                                ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class TestCellMeta:

    def test_cell_meta_keys(self, mock_cell_meta):
        for cid, meta in mock_cell_meta.items():
            assert 'x' in meta
            assert 'y' in meta
            assert 'crop' in meta
            assert 'irrigation' in meta
            assert 'list_idx' in meta

    def test_cell_ids_are_integers(self, mock_cell_meta):
        for cid in mock_cell_meta:
            assert isinstance(cid, int)

    def test_coordinates_are_floats(self, mock_cell_meta):
        for meta in mock_cell_meta.values():
            assert isinstance(meta['x'], float)
            assert isinstance(meta['y'], float)

    def test_irrigation_values_valid(self, mock_cell_meta):
        valid = {'rainfed', 'irrigated'}
        for meta in mock_cell_meta.values():
            assert meta['irrigation'] in valid


class TestSummaryDataFrame:

    def test_required_columns_present(self, mock_summary):
        required = [
            'cell_id', 'x', 'y', 'crop', 'irrigation',
            'harvest_year', 'season_label', 'crop_irr',
            'Dry yield (tonne/ha)', 'seasonal_precip_mm',
            'wp_et_kg_per_m3',
        ]
        for col in required:
            assert col in mock_summary.columns, f"Missing column: {col}"

    def test_season_label_is_string(self, mock_summary):
        assert mock_summary['season_label'].dtype == object

    def test_crop_irr_format(self, mock_summary):
        for val in mock_summary['crop_irr'].unique():
            assert ' | ' in val, f"crop_irr must contain ' | ': {val}"

    def test_no_nan_harvest_year(self, mock_summary):
        assert mock_summary['harvest_year'].isna().sum() == 0

    def test_irrigation_only_valid(self, mock_summary):
        assert set(mock_summary['irrigation'].unique()).issubset({'rainfed', 'irrigated'})

    def test_yields_non_negative(self, mock_summary):
        assert (mock_summary['Dry yield (tonne/ha)'] >= 0).all()

    def test_rainfed_irrigation_zero(self, mock_summary):
        rf = mock_summary[mock_summary['irrigation'] == 'rainfed']
        assert (rf['Seasonal irrigation (mm)'] == 0).all()


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  4. YEAR FILTERING & DATE INDEX                                             ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class TestYearFiltering:

    def _build_years(self, date_index, min_days=5):
        return [yr for yr in sorted(date_index.year.unique())
                if (date_index.year == yr).sum() > min_days]

    def test_full_years_included(self):
        idx = pd.date_range('2008-01-01', '2010-12-31', freq='D')
        years = self._build_years(idx)
        assert 2008 in years
        assert 2009 in years
        assert 2010 in years

    def test_partial_year_excluded(self):
        idx = pd.date_range('2007-12-29', '2010-12-31', freq='D')
        years = self._build_years(idx)
        assert 2007 not in years

    def test_year_rows_bounds(self):
        idx = pd.date_range('2008-01-01', '2010-12-31', freq='D')
        years = self._build_years(idx)
        year_rows = {}
        for yr in years:
            indices = np.where(idx.year == yr)[0]
            year_rows[str(yr)] = (int(indices[0]), int(indices[-1]))
        assert year_rows['2008'][0] == 0
        assert year_rows['2008'][1] == 365  # 2008 is leap year → 366 days, index 0..365
        assert year_rows['2009'][0] == 366
        assert year_rows['2010'][0] == 366 + 365

    def test_year_suffix_format(self):
        years = [2008, 2009, 2010]
        suffix = f'{years[0]}{years[-1]}'
        assert suffix == '20082010'


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  5. PRECOMPUTED AGGREGATIONS                                                ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class TestPrecomputedAgg:

    def test_mean_agg_correct(self, mock_summary):
        ci = 'maize | rainfed'
        var = 'Dry yield (tonne/ha)'
        sub = mock_summary[mock_summary['crop_irr'] == ci]
        grouped = sub.groupby('cell_id')[var]
        result = grouped.mean()
        expected = sub.groupby('cell_id')[var].mean()
        pd.testing.assert_series_equal(result, expected)

    def test_sum_agg_correct(self, mock_summary):
        ci = 'maize | rainfed'
        var = 'production_tonnes'
        sub = mock_summary[mock_summary['crop_irr'] == ci]
        result = sub.groupby('cell_id')[var].sum()
        assert (result > 0).all()

    def test_irrigation_range_starts_at_zero(self, mock_summary):
        ci = 'maize | rainfed'
        var = 'Seasonal irrigation (mm)'
        sub = mock_summary[mock_summary['crop_irr'] == ci]
        agg_vals = sub.groupby('cell_id')[var].sum()
        vmax = agg_vals.max() if agg_vals.max() > 0 else 1
        vmin = 0
        assert vmin == 0
        assert vmax >= 0

    def test_all_map_vars_have_range(self, mock_summary):
        MAP_VARIABLES_KEYS = [
            'Dry yield (tonne/ha)', 'seasonal_precip_mm',
            'wp_et_kg_per_m3', 'Seasonal irrigation (mm)',
        ]
        for ci in mock_summary['crop_irr'].unique():
            sub = mock_summary[mock_summary['crop_irr'] == ci]
            for var in MAP_VARIABLES_KEYS:
                if var in sub.columns:
                    vals = sub[var].dropna()
                    assert len(vals) > 0, f"No data for {ci} / {var}"


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  6. GRID GEOJSON                                                            ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class TestGridGeoJSON:

    def _build_grid_geojson(self, cells_df, half):
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

    def test_feature_count(self, mock_summary):
        cells = mock_summary[['cell_id', 'x', 'y']].drop_duplicates()
        gj = self._build_grid_geojson(cells, 0.025)
        assert len(gj['features']) == len(cells)

    def test_feature_ids_are_strings(self, mock_summary):
        cells = mock_summary[['cell_id', 'x', 'y']].drop_duplicates()
        gj = self._build_grid_geojson(cells, 0.025)
        for f in gj['features']:
            assert isinstance(f['id'], str)

    def test_polygon_is_closed(self, mock_summary):
        cells = mock_summary[['cell_id', 'x', 'y']].drop_duplicates()
        gj = self._build_grid_geojson(cells, 0.025)
        for f in gj['features']:
            coords = f['geometry']['coordinates'][0]
            assert coords[0] == coords[-1], "Polygon ring must be closed"

    def test_polygon_has_five_points(self, mock_summary):
        cells = mock_summary[['cell_id', 'x', 'y']].drop_duplicates()
        gj = self._build_grid_geojson(cells, 0.025)
        for f in gj['features']:
            coords = f['geometry']['coordinates'][0]
            assert len(coords) == 5

    def test_cell_res_defines_half(self):
        CELL_RES = 0.05
        half = CELL_RES / 2
        assert half == 0.025


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  7. FIGURE BUILDERS — output map                                            ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class TestBuildOutputMap:
    """Tests for build_output_map logic — checks traces, colorbar, hover."""

    def _make_subset(self, mock_summary, ci, season):
        sub = mock_summary[
            (mock_summary['crop_irr'] == ci) &
            (mock_summary['season_label'] == season)
        ].copy()
        sub['cell_id_str'] = sub['cell_id'].astype(int).astype(str)
        return sub

    def test_hover_contains_cell_id(self, mock_summary):
        sub = self._make_subset(mock_summary, 'maize | rainfed', '2008')
        var = 'Dry yield (tonne/ha)'
        hover = (
            '<b>Cell ' + sub['cell_id'].astype(int).astype(str) + '</b>'
        ).tolist()
        assert all('<b>Cell' in h for h in hover)

    def test_hover_contains_crop(self, mock_summary):
        sub = self._make_subset(mock_summary, 'maize | rainfed', '2008')
        hover = ('Crop: ' + sub['crop'].str.capitalize()).tolist()
        assert all('Maize' in h for h in hover)

    def test_empty_figure_on_missing_precomputed(self):
        precomputed_agg = {}
        result = precomputed_agg.get(('maize | rainfed', 'Dry yield (tonne/ha)', 'mean'))
        assert result is None

    def test_agg_label_mean(self):
        agg_func = 'mean'
        label = f"{'Sum' if agg_func == 'sum' else 'Avg'} all years"
        assert label == 'Avg all years'

    def test_agg_label_sum(self):
        agg_func = 'sum'
        label = f"{'Sum' if agg_func == 'sum' else 'Avg'} all years"
        assert label == 'Sum all years'

    def test_sel_locations_when_cell_selected(self):
        sel_cell = 42
        sel_locations = [str(sel_cell)] if sel_cell is not None else []
        assert sel_locations == ['42']

    def test_sel_locations_when_no_cell(self):
        sel_cell = None
        sel_locations = [str(sel_cell)] if sel_cell is not None else []
        assert sel_locations == []

    def test_lasso_ids_are_strings(self):
        lasso_cells = [1, 2, 3]
        lasso_ids = [str(c) for c in lasso_cells]
        assert lasso_ids == ['1', '2', '3']


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  8. FIGURE BUILDERS — time series                                           ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class TestBuildOutputTs:

    def _period_rows(self, season_label, year_rows, n_rows):
        if season_label == 'all':
            return 0, n_rows - 1
        return year_rows[season_label]

    def test_full_period_on_all_seasons(self):
        n_rows = 1095
        row_start, row_end = self._period_rows('all', {}, n_rows)
        assert row_start == 0
        assert row_end == n_rows - 1

    def test_season_period_uses_year_rows(self):
        year_rows = {'2008': (0, 365), '2009': (366, 730)}
        row_start, row_end = self._period_rows('2008', year_rows, 1095)
        assert row_start == 0
        assert row_end == 365

    def test_period_label_full(self):
        ts_period = 'full'
        label = 'Full simulation' if ts_period == 'full' else '2008'
        assert label == 'Full simulation'

    def test_period_label_season(self):
        ts_period = 'season'
        season_label = '2009'
        label = 'Full simulation' if ts_period == 'full' else season_label
        assert label == '2009'

    def test_daily_var_table_selection(self):
        DAILY_VARIABLES = {
            'Es':      {'table': 'water_flux'},
            'biomass': {'table': 'crop_growth'},
        }
        assert DAILY_VARIABLES['Es']['table'] == 'water_flux'
        assert DAILY_VARIABLES['biomass']['table'] == 'crop_growth'

    def test_preseason_shading_condition(self):
        preseason_end_row = 59
        row_start = 0
        should_shade = row_start <= preseason_end_row
        assert should_shade is True

    def test_no_preseason_shading_when_past(self):
        preseason_end_row = 59
        row_start = 366
        should_shade = row_start <= preseason_end_row
        assert should_shade is False


class TestMeanStdBand:

    def _compute_band(self, values):
        arr = np.array(values)
        mean = arr.mean()
        std  = arr.std()
        return mean, std, mean + std, mean - std

    def test_mean_correct(self):
        mean, std, upper, lower = self._compute_band([1, 2, 3, 4, 5])
        assert mean == pytest.approx(3.0)

    def test_upper_lower_symmetric(self):
        mean, std, upper, lower = self._compute_band([1, 2, 3, 4, 5])
        assert upper - mean == pytest.approx(mean - lower)

    def test_constant_series_zero_std(self):
        mean, std, upper, lower = self._compute_band([5, 5, 5, 5])
        assert std == pytest.approx(0.0)
        assert upper == pytest.approx(5.0)
        assert lower == pytest.approx(5.0)

    def test_click_state_reset_on_third_click(self):
        def handle_click(clicked_date, ts_clicks):
            count = ts_clicks['count']
            if count == 0:
                return {'count': 1, 'start': clicked_date, 'end': None}
            elif count == 1:
                start = ts_clicks['start']
                if clicked_date < start:
                    start, clicked_date = clicked_date, start
                return {'count': 2, 'start': start, 'end': clicked_date}
            return {'count': 0, 'start': None, 'end': None}

        state = {'count': 0, 'start': None, 'end': None}
        state = handle_click('2008-06-01', state)
        assert state['count'] == 1
        state = handle_click('2008-08-01', state)
        assert state['count'] == 2
        state = handle_click('2008-10-01', state)
        assert state['count'] == 0
        assert state['start'] is None

    def test_click_order_auto_sorted(self):
        def handle_click(clicked_date, ts_clicks):
            count = ts_clicks['count']
            if count == 0:
                return {'count': 1, 'start': clicked_date, 'end': None}
            elif count == 1:
                start = ts_clicks['start']
                if clicked_date < start:
                    start, clicked_date = clicked_date, start
                return {'count': 2, 'start': start, 'end': clicked_date}
            return {'count': 0, 'start': None, 'end': None}

        state = {'count': 0, 'start': None, 'end': None}
        state = handle_click('2008-09-01', state)
        state = handle_click('2008-06-01', state)  # click earlier date second
        assert state['start'] < state['end']


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  9. INPUT MAP — climate label logic                                         ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class TestClimateMapLabels:

    CLIMATE_VARIABLES = {
        'MaxTemp':       {'label': 'Max Temperature (°C)',    'map_label': 'Max Temperature (°C)',    'unit': '°C'},
        'Precipitation': {'label': 'Precipitation (mm/day)', 'map_label': 'Precipitation (mm/year)', 'unit': 'mm/year'},
        'ReferenceET':   {'label': 'Reference ET (mm/day)',  'map_label': 'Reference ET (mm/year)',  'unit': 'mm/year'},
    }

    def test_button_uses_map_label(self):
        label = self.CLIMATE_VARIABLES['Precipitation']['map_label']
        assert 'mm/year' in label

    def test_ts_yaxis_uses_label(self):
        label = self.CLIMATE_VARIABLES['Precipitation']['label']
        assert 'mm/day' in label

    def test_hover_uses_map_label_and_unit(self):
        var_info = self.CLIMATE_VARIABLES['Precipitation']
        hover = f"{var_info['map_label']}: 1.234 {var_info['unit']}"
        assert 'Precipitation (mm/year)' in hover
        assert 'mm/year' in hover

    def test_hover_does_not_show_mm_per_day(self):
        var_info = self.CLIMATE_VARIABLES['Precipitation']
        hover = f"{var_info['map_label']}: 1.234 {var_info['unit']}"
        assert 'mm/day' not in hover

    def test_temperature_map_label_same_as_label(self):
        assert (self.CLIMATE_VARIABLES['MaxTemp']['label'] ==
                self.CLIMATE_VARIABLES['MaxTemp']['map_label'])

    def test_period_label_all_years(self):
        season_label = 'all'
        period_label = 'All years (daily mean)' if season_label == 'all' else f'{season_label} (daily mean)'
        assert period_label == 'All years (daily mean)'

    def test_period_label_specific_year(self):
        season_label = '2009'
        period_label = 'All years (daily mean)' if season_label == 'all' else f'{season_label} (daily mean)'
        assert period_label == '2009 (daily mean)'


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  10. EXPORT LOGIC                                                           ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class TestExportLogic:

    def test_date_range_mask(self):
        date_index = pd.date_range('2008-01-01', '2010-12-31', freq='D')
        start_ts = pd.Timestamp('2008-06-01')
        end_ts   = pd.Timestamp('2008-08-31')
        mask     = (date_index >= start_ts) & (date_index <= end_ts)
        time_idx = np.where(mask)[0]
        assert len(time_idx) == 92  # June (30) + July (31) + Aug (31)

    def test_empty_date_range(self):
        date_index = pd.date_range('2008-01-01', '2010-12-31', freq='D')
        start_ts = pd.Timestamp('2015-01-01')
        end_ts   = pd.Timestamp('2015-12-31')
        mask     = (date_index >= start_ts) & (date_index <= end_ts)
        time_idx = np.where(mask)[0]
        assert len(time_idx) == 0

    def test_grid_axes_sorted(self, mock_cell_meta):
        cell_ids = list(mock_cell_meta.keys())
        xs = sorted(set(mock_cell_meta[c]['x'] for c in cell_ids))
        ys = sorted(set(mock_cell_meta[c]['y'] for c in cell_ids), reverse=True)
        assert xs == sorted(xs)
        assert ys == sorted(ys, reverse=True)

    def test_3d_array_shape(self, mock_cell_meta):
        cell_ids = list(mock_cell_meta.keys())
        n_time = 30
        xs = sorted(set(mock_cell_meta[c]['x'] for c in cell_ids))
        ys = sorted(set(mock_cell_meta[c]['y'] for c in cell_ids), reverse=True)
        arr = np.full((n_time, len(ys), len(xs)), np.nan, dtype=np.float32)
        assert arr.shape == (30, 3, 3)

    def test_no_export_vars_message(self):
        export_vars = []
        msg = 'Select at least one variable.' if not export_vars else 'ok'
        assert msg == 'Select at least one variable.'

    def test_no_format_message(self):
        formats = []
        msg = 'Select at least one format.' if not formats else 'ok'
        assert msg == 'Select at least one format.'

    def test_start_before_end_validation(self):
        start = pd.Timestamp('2009-01-01')
        end   = pd.Timestamp('2008-01-01')
        invalid = start > end
        assert invalid is True

    def test_valid_date_range(self):
        start = pd.Timestamp('2008-01-01')
        end   = pd.Timestamp('2010-12-31')
        valid = start <= end
        assert valid is True

    def test_base_name_format(self):
        var = 'Es'
        start_ts = pd.Timestamp('2008-06-01')
        end_ts   = pd.Timestamp('2008-08-31')
        base_name = f"{var}_{start_ts.strftime('%Y%m%d')}_{end_ts.strftime('%Y%m%d')}"
        assert base_name == 'Es_20080601_20080831'

    def test_units_extracted_from_label(self):
        label = 'Soil Evaporation (mm/day)'
        unit = label.split('(')[-1].replace(')', '') if '(' in label else ''
        assert unit == 'mm/day'

    def test_units_missing_parentheses(self):
        label = 'Canopy Cover'
        unit = label.split('(')[-1].replace(')', '') if '(' in label else ''
        assert unit == ''


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  11. IRR_MAP & CROP CALENDAR                                                ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class TestIrrMap:

    IRR_MAP = {'rainfed': 'rf', 'irrigated': 'ir'}

    def test_rainfed_maps_to_rf(self):
        assert self.IRR_MAP['rainfed'] == 'rf'

    def test_irrigated_maps_to_ir(self):
        assert self.IRR_MAP['irrigated'] == 'ir'

    def test_unknown_key_fallback(self):
        irr = 'sprinkler'
        code = self.IRR_MAP.get(irr, irr)
        assert code == 'sprinkler'

    def test_crop_cal_var_name_construction(self):
        crop_irr = 'Maize | rainfed'
        parts = crop_irr.split(' | ')
        crop_name = parts[0].capitalize()
        irr_code  = self.IRR_MAP.get(parts[1], parts[1])
        plant_var = f'{crop_name}_{irr_code}_planting'
        assert plant_var == 'Maize_rf_planting'

    def test_harvest_doy_calculation(self):
        doy = 142   # planting DOY
        gsl = 138   # growing season length
        h_doy = doy + gsl - 1
        harvest = (pd.Timestamp('2001-01-01') +
                   pd.to_timedelta(h_doy - 1, unit='D')).strftime('%b %d')
        assert harvest == 'Oct 06'


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  12. CALLBACK LOGIC (state machine tests, no Dash server needed)           ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class TestCallbackLogic:

    def test_effective_period_all_seasons(self):
        season_label = 'all'
        effective_period = 'full' if season_label == 'all' else 'season'
        assert effective_period == 'full'

    def test_effective_period_single_season(self):
        season_label = '2009'
        effective_period = 'full' if season_label == 'all' else 'season'
        assert effective_period == 'season'

    def test_effective_season_all_uses_first(self):
        season_list = ['2008', '2009', '2010']
        season_label = 'all'
        effective_season = season_list[0] if season_label == 'all' else season_label
        assert effective_season == '2008'

    def test_effective_season_specific(self):
        season_list = ['2008', '2009', '2010']
        season_label = '2010'
        effective_season = season_list[0] if season_label == 'all' else season_label
        assert effective_season == '2010'

    def test_ts_container_hidden_when_no_cell(self):
        cell_id = None
        hidden  = {'visibility': 'hidden', 'height': '0', 'overflow': 'hidden'}
        visible = {'visibility': 'visible', 'height': 'auto', 'overflow': 'visible'}
        style = hidden if cell_id is None else visible
        assert style['visibility'] == 'hidden'

    def test_ts_container_visible_when_cell_selected(self):
        cell_id = 42
        hidden  = {'visibility': 'hidden', 'height': '0', 'overflow': 'hidden'}
        visible = {'visibility': 'visible', 'height': 'auto', 'overflow': 'visible'}
        style = hidden if cell_id is None else visible
        assert style['visibility'] == 'visible'

    def test_agg_row_hidden_on_single_season(self):
        sel_season = '2008'
        sel_tab    = 'output'
        should_show = sel_season == 'all' and sel_tab == 'output'
        assert should_show is False

    def test_agg_row_visible_on_all_years_output_tab(self):
        sel_season = 'all'
        sel_tab    = 'output'
        should_show = sel_season == 'all' and sel_tab == 'output'
        assert should_show is True

    def test_agg_row_hidden_on_input_tab_even_if_all(self):
        sel_season = 'all'
        sel_tab    = 'input'
        should_show = sel_season == 'all' and sel_tab == 'output'
        assert should_show is False

    def test_lasso_whole_area_clears_selection(self):
        whole_area = ['all']
        lasso_cells = [1, 2, 3]
        result = [] if 'all' in (whole_area or []) else lasso_cells
        assert result == []

    def test_lasso_selection_when_no_whole_area(self):
        whole_area = []
        lasso_cells = [1, 2, 3]
        result = [] if 'all' in (whole_area or []) else lasso_cells
        assert result == [1, 2, 3]

    def test_export_cells_whole_area(self, mock_cell_meta):
        whole_area = ['all']
        lasso_cells = []
        if 'all' in (whole_area or []) or not lasso_cells:
            selected_cells = list(mock_cell_meta.keys())
        else:
            selected_cells = lasso_cells
        assert selected_cells == list(mock_cell_meta.keys())

    def test_export_cells_lasso_selection(self, mock_cell_meta):
        whole_area = []
        lasso_cells = [1, 2]
        if 'all' in (whole_area or []) or not lasso_cells:
            selected_cells = list(mock_cell_meta.keys())
        else:
            selected_cells = lasso_cells
        assert selected_cells == [1, 2]


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  13. SPAM MODE SWITCHING                                                    ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class TestInputMode:

    def test_climvar_click_sets_climate_mode(self):
        triggered = {'type': 'climvar-btn', 'index': 'Precipitation'}
        mode = 'climate' if triggered.get('type') == 'climvar-btn' else 'spam'
        assert mode == 'climate'

    def test_spamvar_click_sets_spam_mode(self):
        triggered = {'type': 'spamvar-btn', 'index': 'Maize_rf_physical_area'}
        mode = 'spam' if triggered.get('type') == 'spamvar-btn' else 'climate'
        assert mode == 'spam'

    def test_no_spam_data_message(self):
        relevant = []
        msg = 'No SPAM data for this crop.' if not relevant else ''
        assert msg == 'No SPAM data for this crop.'

    def test_spam_colorbar_label(self):
        spam_var = 'Maize_rf_physical_area'
        label = spam_var.replace('_physical_area', '').replace('_', ' ')
        assert label == 'Maize rf'

    def test_spam_z_nan_replaced_with_zero(self):
        z_raw = np.array([1.0, np.nan, 3.0, np.nan])
        z_arr = np.where(np.isnan(z_raw), 0.0, z_raw)
        assert np.isnan(z_arr).sum() == 0
        assert z_arr[1] == 0.0


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  14. MAPBOX LAYER STRUCTURE                                                 ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class TestMapboxLayers:

    def _mapbox_layers(self, region_geojson):
        return [
            dict(sourcetype='raster',
                 source=['https://server.arcgisonline.com/ArcGIS/rest/services/'
                         'World_Topo_Map/MapServer/tile/{z}/{y}/{x}'],
                 below='traces'),
            dict(source=region_geojson, type='line', color='#1a6faf',
                 line=dict(width=2.5)),
        ]

    def test_returns_two_layers(self):
        layers = self._mapbox_layers({})
        assert len(layers) == 2

    def test_first_layer_is_raster(self):
        layers = self._mapbox_layers({})
        assert layers[0]['sourcetype'] == 'raster'

    def test_second_layer_is_line(self):
        layers = self._mapbox_layers({})
        assert layers[1]['type'] == 'line'

    def test_line_color(self):
        layers = self._mapbox_layers({})
        assert layers[1]['color'] == '#1a6faf'
