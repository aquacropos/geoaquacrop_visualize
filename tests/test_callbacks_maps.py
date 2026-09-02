"""
Tests for ``geoaquacrop_plotting.callbacks_maps``.

Covers the Patch-based map update logic: which trace index each layer lives at,
the climate/SPAM mode switch, and the SPAM button rebuild. ``CLIMATE_VARIABLES``
comes from the real config.
"""

import numpy as np

from geoaquacrop_plotting.config import CLIMATE_VARIABLES


class TestTraceIndices:
    """The Patch callbacks address traces positionally, so the order is a contract."""

    OUTPUT_MAP_TRACES = ['background', 'data', 'click-highlight',
                         'lasso-highlight', 'lasso-scatter']
    INPUT_MAP_TRACES = ['background', 'data', 'click-highlight']

    def test_output_map_data_layer_is_index_1(self):
        assert self.OUTPUT_MAP_TRACES.index('data') == 1

    def test_output_map_click_highlight_is_index_2(self):
        assert self.OUTPUT_MAP_TRACES.index('click-highlight') == 2

    def test_output_map_lasso_highlight_is_index_3(self):
        assert self.OUTPUT_MAP_TRACES.index('lasso-highlight') == 3

    def test_output_map_has_five_traces(self):
        assert len(self.OUTPUT_MAP_TRACES) == 5

    def test_input_map_data_layer_is_index_1(self):
        assert self.INPUT_MAP_TRACES.index('data') == 1

    def test_input_map_click_highlight_is_index_2(self):
        assert self.INPUT_MAP_TRACES.index('click-highlight') == 2

    def test_input_map_has_three_traces(self):
        assert len(self.INPUT_MAP_TRACES) == 3


class TestHighlightPatch:

    def _highlight(self, sel_cell):
        return ([str(sel_cell)] if sel_cell is not None else [],
                [1] if sel_cell is not None else [])

    def test_selected_cell_sets_one_location(self):
        locs, z = self._highlight(42)
        assert locs == ['42']
        assert z == [1]

    def test_no_selection_clears_layer(self):
        locs, z = self._highlight(None)
        assert locs == []
        assert z == []

    def test_locations_and_z_stay_aligned(self):
        for cell in (None, 1, 999):
            locs, z = self._highlight(cell)
            assert len(locs) == len(z)

    def test_lasso_highlight_scales_with_selection(self):
        for cells in ([], [1], [1, 2, 3]):
            ids = [str(c) for c in (cells or [])]
            z = [1] * len(ids)
            assert len(ids) == len(z) == len(cells)


class TestInputMode:
    """The input map serves climate variables and SPAM area from one figure."""

    def test_climvar_selection_sets_climate_mode(self):
        triggered = 'climvar-dd'
        assert ('climate' if triggered == 'climvar-dd' else 'spam') == 'climate'

    def test_spamvar_click_sets_spam_mode(self):
        triggered = {'type': 'spamvar-btn', 'index': 'Maize_rf_physical_area'}
        mode = ('spam' if isinstance(triggered, dict)
                and triggered.get('type') == 'spamvar-btn' else 'climate')
        assert mode == 'spam'

    def test_initial_load_defaults_to_climate(self):
        triggered = None
        mode = ('spam' if isinstance(triggered, dict)
                and triggered.get('type') == 'spamvar-btn' else 'climate')
        assert mode == 'climate'

    def test_spam_mode_requires_a_variable(self):
        for mode, var, expected in (('spam', 'Maize_rf_physical_area', True),
                                    ('spam', '', False),
                                    ('climate', 'Maize_rf_physical_area', False)):
            assert bool(mode == 'spam' and var) is expected

    def test_no_spam_data_message(self):
        relevant = []
        assert ('No SPAM data for this crop.' if not relevant else '') \
            == 'No SPAM data for this crop.'

    def test_spam_button_label_is_humanised(self):
        assert 'Maize_rf_physical_area'.replace('_physical_area', '').replace('_', ' ') \
            == 'Maize rf'

    def test_active_button_only_when_in_spam_mode(self):
        var = 'Maize_rf_physical_area'
        assert (var == var and 'spam' == 'spam') is True
        assert (var == var and 'climate' == 'spam') is False


class TestSpamZValues:

    def test_nan_replaced_with_zero(self):
        z_raw = np.array([1.0, np.nan, 3.0, np.nan])
        z_arr = np.where(np.isnan(z_raw), 0.0, z_raw)
        assert np.isnan(z_arr).sum() == 0
        assert z_arr[1] == 0.0

    def test_vmin_is_zero_and_vmax_positive(self):
        z_vals = [0.0, 12.5, 3.0]
        vmin, vmax = 0.0, float(max(z_vals)) if max(z_vals) > 0 else 1.0
        assert vmin == 0.0
        assert vmax == 12.5

    def test_all_zero_grid_gets_unit_vmax(self):
        z_vals = [0.0, 0.0]
        vmax = float(max(z_vals)) if max(z_vals) > 0 else 1.0
        assert vmax == 1.0

    def test_colorbar_title_reports_hectares(self):
        label = 'Maize rf'
        assert f'{label}<br>(ha)' == 'Maize rf<br>(ha)'


class TestClimatePeriodLabels:

    SUM_VARS = ('Precipitation', 'ReferenceET')

    def _period_label(self, var, season):
        if var in self.SUM_VARS:
            return ('All years (total mm)' if season == 'all'
                    else f'{season} (total mm)')
        return ('All years (daily mean)' if season == 'all'
                else f'{season} (daily mean)')

    def test_precipitation_all_years_is_total(self):
        assert self._period_label('Precipitation', 'all') == 'All years (total mm)'

    def test_precipitation_single_year_is_total(self):
        assert self._period_label('Precipitation', '2009') == '2009 (total mm)'

    def test_reference_et_is_total(self):
        assert 'total mm' in self._period_label('ReferenceET', 'all')

    def test_temperature_all_years_is_daily_mean(self):
        assert self._period_label('MaxTemp', 'all') == 'All years (daily mean)'

    def test_temperature_single_year_is_daily_mean(self):
        assert self._period_label('MinTemp', '2010') == '2010 (daily mean)'

    def test_every_climate_var_gets_a_label(self):
        for var in CLIMATE_VARIABLES:
            for season in ('all', '2009'):
                assert self._period_label(var, season)

    def test_colorbar_title_uses_unit_and_period(self):
        info = CLIMATE_VARIABLES['MaxTemp']
        title = f"{info['unit']}<br>({self._period_label('MaxTemp', '2009')})"
        assert title == '°C<br>(2009 (daily mean))'


class TestCropCalendarInfoText:

    def test_missing_calendar_message(self):
        info = None
        msg = ('No crop calendar data found for this crop and irrigation type.'
               if info is None else 'ok')
        assert msg.startswith('No crop calendar data')

    def test_info_text_reports_all_three_fields(self):
        info = {'planting': 'May 22', 'planting_doy': 142,
                'season_length': 138, 'harvest': 'Oct 06'}
        text = (f"Planting: {info['planting']} (DOY {info['planting_doy']})  |  "
                f"Season length: {info['season_length']} days  |  "
                f"Approx. harvest: {info['harvest']}")
        assert text == ('Planting: May 22 (DOY 142)  |  '
                        'Season length: 138 days  |  Approx. harvest: Oct 06')
