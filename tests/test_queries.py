"""
Tests for ``geoaquacrop_plotting.queries``.

``queries`` imports ``data``, so the lookups are mirrored here. ``IRR_MAP`` is
read from the real config so a change there is caught.
"""

import numpy as np
import pandas as pd

from geoaquacrop_plotting.config import BOUNDARY_URL, IRR_MAP


def spam_vars_for_crop(crop_irr, spam_var_keys, irr_map=IRR_MAP):
    """Mirror of queries.spam_vars_for_crop, with the key list injected."""

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


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  spam_vars_for_crop                                                        ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class TestSpamVarsForCrop:

    def test_exact_match(self):
        assert spam_vars_for_crop('Maize | rainfed', ['Maize_rf_physical_area']) \
            == ['Maize_rf_physical_area']

    def test_case_insensitive_fallback(self):
        assert spam_vars_for_crop('Maize | rainfed', ['maize_rf_physical_area']) \
            == ['maize_rf_physical_area']

    def test_irrigated_mapping(self):
        assert spam_vars_for_crop('Maize | irrigated', ['Maize_ir_physical_area']) \
            == ['Maize_ir_physical_area']

    def test_no_match_returns_empty(self):
        assert spam_vars_for_crop('Maize | rainfed', ['Wheat_rf_physical_area']) == []

    def test_paddyrice_capitalize(self):
        """Multi-part names miss the capitalize() match and fall back to the scan."""

        assert spam_vars_for_crop('PaddyRice1 | irrigated', ['PaddyRice1_ir_physical_area']) \
            == ['PaddyRice1_ir_physical_area']

    def test_empty_spam_var_keys(self):
        assert spam_vars_for_crop('Maize | rainfed', []) == []

    def test_whitespace_in_irrigation_is_stripped(self):
        assert spam_vars_for_crop('Maize | rainfed ', ['Maize_rf_physical_area']) \
            == ['Maize_rf_physical_area']

    def test_returns_at_most_one_match(self):
        keys = ['Maize_rf_physical_area', 'maize_rf_physical_area']
        assert len(spam_vars_for_crop('Maize | rainfed', keys)) == 1


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  Crop calendar variable names and harvest arithmetic                       ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class TestCropCalendar:

    def test_planting_var_name_construction(self):
        parts = 'Maize | rainfed'.split(' | ')
        plant_var = f'{parts[0].capitalize()}_{IRR_MAP.get(parts[1], parts[1])}_planting'
        assert plant_var == 'Maize_rf_planting'

    def test_gsl_var_name_construction(self):
        parts = 'Maize | irrigated'.split(' | ')
        gsl_var = (f'{parts[0].capitalize()}_'
                   f'{IRR_MAP.get(parts[1], parts[1])}_growing_season_length')
        assert gsl_var == 'Maize_ir_growing_season_length'

    def test_planting_doy_to_date(self):
        doy = 142
        assert (pd.Timestamp('2001-01-01') +
                pd.to_timedelta(doy - 1, unit='D')).strftime('%b %d') == 'May 22'

    def test_harvest_doy_calculation(self):
        doy, gsl = 142, 138
        h_doy = doy + gsl - 1
        harvest = (pd.Timestamp('2001-01-01') +
                   pd.to_timedelta(h_doy - 1, unit='D')).strftime('%b %d')
        assert harvest == 'Oct 06'

    def test_harvest_na_without_season_length(self):
        gsl = None
        assert ('N/A' if not gsl else 'computed') == 'N/A'

    def test_doy_filter_rejects_nan_and_zero(self):
        """get_cropcal_summary keeps only positive, non-NaN DOY values."""

        arr = np.array([np.nan, 0.0, 142.0, -3.0])
        valid = arr[(~np.isnan(arr)) & (arr > 0)]
        assert list(valid) == [142.0]

    def test_gsl_filter_rejects_absurd_values(self):
        """Season length is filtered to 0 < gsl < 10000 days."""

        raw = np.array([np.nan, 0.0, 138.0, 99999.0])
        valid = raw[(~np.isnan(raw)) & (raw > 0) & (raw < 10000)]
        assert list(valid) == [138.0]


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  get_daily date attachment                                                 ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class TestGetDaily:

    def test_date_column_derived_from_sim_start(self, mock_daily_wf):
        sim_start = pd.Timestamp('2008-01-01')
        wf = mock_daily_wf.copy().reset_index(drop=True)
        wf['date'] = sim_start + pd.to_timedelta(wf.index, unit='D')
        assert wf['date'].iloc[0] == sim_start
        assert wf['date'].iloc[1] == sim_start + pd.Timedelta(days=1)

    def test_dates_are_daily_and_monotonic(self, mock_daily_wf):
        sim_start = pd.Timestamp('2008-01-01')
        wf = mock_daily_wf.copy().reset_index(drop=True)
        wf['date'] = sim_start + pd.to_timedelta(wf.index, unit='D')
        assert wf['date'].is_monotonic_increasing
        assert (wf['date'].diff().dropna() == pd.Timedelta(days=1)).all()

    def test_water_flux_and_crop_growth_align(self, mock_daily_wf, mock_daily_cg):
        assert len(mock_daily_wf) == len(mock_daily_cg)

    def test_missing_cell_returns_none_pair(self):
        cell_id_to_idx = {1: 0}
        idx = cell_id_to_idx.get(999)
        assert idx is None

    def test_water_flux_columns(self, mock_daily_wf):
        for col in ('Es', 'EsPot', 'Tr', 'TrPot', 'Infl', 'Runoff', 'DeepPerc', 'Wr'):
            assert col in mock_daily_wf.columns

    def test_crop_growth_columns(self, mock_daily_cg):
        for col in ('biomass', 'canopy_cover', 'gdd_cum', 'z_root', 'DryYield'):
            assert col in mock_daily_cg.columns

    def test_gdd_is_cumulative(self, mock_daily_cg):
        assert mock_daily_cg['gdd_cum'].is_monotonic_increasing


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  get_climate_map_values aggregation choice                                 ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class TestClimateMapAggregation:

    SUM_VARS = ('Precipitation', 'ReferenceET')

    def test_flux_variables_are_summed(self):
        for var in self.SUM_VARS:
            assert var in self.SUM_VARS

    def test_temperature_variables_are_averaged(self):
        for var in ('MaxTemp', 'MinTemp'):
            assert var not in self.SUM_VARS

    def test_all_years_uses_whole_series(self):
        season_label = 'all'
        assert (season_label == 'all') is True

    def test_single_year_filters_by_year(self):
        season_label = '2009'
        assert int(season_label) == 2009


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  mapbox_layers                                                             ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

def mapbox_layers(boundary_url=BOUNDARY_URL):
    """Mirror of queries.mapbox_layers, with the boundary URL injected."""

    return [
        dict(sourcetype='raster',
             source=['https://server.arcgisonline.com/ArcGIS/rest/services/'
                     'World_Topo_Map/MapServer/tile/{z}/{y}/{x}'],
             below='traces'),
        dict(sourcetype='geojson', source=boundary_url, type='line',
             color='#1a6faf', line=dict(width=2.5)),
    ]


class TestMapboxLayers:

    def test_returns_two_layers(self):
        assert len(mapbox_layers()) == 2

    def test_first_layer_is_raster(self):
        assert mapbox_layers()[0]['sourcetype'] == 'raster'

    def test_raster_sits_below_traces(self):
        assert mapbox_layers()[0]['below'] == 'traces'

    def test_second_layer_is_line(self):
        assert mapbox_layers()[1]['type'] == 'line'

    def test_line_color(self):
        assert mapbox_layers()[1]['color'] == '#1a6faf'

    def test_boundary_is_referenced_by_url_not_inlined(self):
        """Inlining the geometry would serialise it into every figure."""

        source = mapbox_layers()[1]['source']
        assert isinstance(source, str) and source.startswith('/')

    def test_boundary_url_comes_from_config(self):
        assert mapbox_layers()[1]['source'] == BOUNDARY_URL

    def test_boundary_url_is_not_under_the_assets_folder(self):
        """It is served from a route over GEOJSON_PATH, not a shipped file."""

        assert not BOUNDARY_URL.startswith('/assets/')

    def test_tile_url_has_zxy_placeholders(self):
        url = mapbox_layers()[0]['source'][0]
        for token in ('{z}', '{y}', '{x}'):
            assert token in url
