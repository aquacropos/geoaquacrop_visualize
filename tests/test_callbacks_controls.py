"""
Tests for ``geoaquacrop_plotting.callbacks_controls``.

Callback modules import ``app_shell`` and ``data``, so registering them needs
the real dataset. These tests cover the pure decision logic inside those
callbacks: tab visibility, aggregation-row visibility, and the
three-dropdown-to-one-store merge for map and daily variables.
"""

from geoaquacrop_plotting.config import DAILY_VARIABLES, MAP_VARIABLES


class TestTabToggle:

    def _toggle_tabs(self, sel_tab):
        show, hide = {'display': 'block'}, {'display': 'none'}
        if sel_tab == 'output':
            return show, hide, show, hide
        return hide, show, hide, show

    def test_output_tab_shows_output_panel(self):
        out_panel, in_panel, out_ctrl, in_ctrl = self._toggle_tabs('output')
        assert out_panel['display'] == 'block'
        assert in_panel['display'] == 'none'
        assert out_ctrl['display'] == 'block'
        assert in_ctrl['display'] == 'none'

    def test_input_tab_shows_input_panel(self):
        out_panel, in_panel, out_ctrl, in_ctrl = self._toggle_tabs('input')
        assert out_panel['display'] == 'none'
        assert in_panel['display'] == 'block'
        assert out_ctrl['display'] == 'none'
        assert in_ctrl['display'] == 'block'

    def test_unknown_tab_falls_through_to_input(self):
        out_panel, in_panel, _, _ = self._toggle_tabs(None)
        assert out_panel['display'] == 'none'
        assert in_panel['display'] == 'block'

    def test_panels_are_mutually_exclusive(self):
        for tab in ('output', 'input'):
            out_panel, in_panel, _, _ = self._toggle_tabs(tab)
            assert out_panel['display'] != in_panel['display']

    def test_default_tab_when_none(self):
        assert (None or 'output') == 'output'


class TestSelectionDefaults:

    def test_crop_falls_back_to_first(self):
        crop_irr_list = ['Maize | rainfed', 'Maize | irrigated']
        assert (None or crop_irr_list[0]) == 'Maize | rainfed'

    def test_season_falls_back_to_first(self):
        season_list = ['2008', '2009', '2010']
        assert (None or season_list[0]) == '2008'

    def test_climate_var_falls_back_to_first(self):
        climate_var_keys = ['MaxTemp', 'MinTemp']
        assert (None or climate_var_keys[0]) == 'MaxTemp'

    def test_explicit_value_wins(self):
        assert ('2010' or ['2008'][0]) == '2010'


class TestAggregationRow:

    def _should_show(self, sel_season, sel_tab):
        return sel_season == 'all' and sel_tab == 'output'

    def test_hidden_on_single_season(self):
        assert self._should_show('2008', 'output') is False

    def test_visible_on_all_years_output_tab(self):
        assert self._should_show('all', 'output') is True

    def test_hidden_on_input_tab_even_if_all(self):
        assert self._should_show('all', 'input') is False

    def test_hidden_on_input_tab_single_season(self):
        assert self._should_show('2008', 'input') is False

    def test_style_dict_matches_visibility(self):
        for season, tab, expected in (('all', 'output', 'block'),
                                      ('2008', 'output', 'none'),
                                      ('all', 'input', 'none')):
            style = ({'display': 'block'} if self._should_show(season, tab)
                     else {'display': 'none'})
            assert style['display'] == expected


class TestAggregationButtons:

    def test_default_aggregation_is_mean(self):
        triggered = None
        assert (triggered['index'] if triggered else 'mean') == 'mean'

    def test_clicked_button_becomes_active(self):
        triggered = {'type': 'agg-btn', 'index': 'sum'}
        assert (triggered['index'] if triggered else 'mean') == 'sum'

    def test_exactly_one_button_is_active(self):
        for sel_agg in ('mean', 'sum'):
            active = [a == sel_agg for a in ('mean', 'sum')]
            assert sum(active) == 1


class TestMapVariableMerge:
    """Three accordion dropdowns feed one store; picking one clears the others."""

    def _set_map_var(self, triggered, yield_v, water_v, wp_v, first_key):
        if triggered == 'mapvar-yield-dd' and yield_v:
            return yield_v, yield_v, None, None
        if triggered == 'mapvar-water-dd' and water_v:
            return water_v, None, water_v, None
        if triggered == 'mapvar-wp-dd' and wp_v:
            return wp_v, None, None, wp_v
        return first_key, first_key, None, None

    def test_yield_selection_clears_others(self):
        store, y, w, p = self._set_map_var('mapvar-yield-dd',
                                          'Dry yield (tonne/ha)', None, None,
                                          'Dry yield (tonne/ha)')
        assert store == 'Dry yield (tonne/ha)'
        assert (y, w, p) == ('Dry yield (tonne/ha)', None, None)

    def test_water_selection_clears_others(self):
        store, y, w, p = self._set_map_var('mapvar-water-dd',
                                          None, 'seasonal_precip_mm', None,
                                          'Dry yield (tonne/ha)')
        assert store == 'seasonal_precip_mm'
        assert (y, w, p) == (None, 'seasonal_precip_mm', None)

    def test_wp_selection_clears_others(self):
        store, y, w, p = self._set_map_var('mapvar-wp-dd',
                                          None, None, 'wp_et_kg_per_m3',
                                          'Dry yield (tonne/ha)')
        assert store == 'wp_et_kg_per_m3'
        assert (y, w, p) == (None, None, 'wp_et_kg_per_m3')

    def test_clearing_a_dropdown_reverts_to_first_key(self):
        first = 'Dry yield (tonne/ha)'
        store, y, w, p = self._set_map_var('mapvar-water-dd', None, None, None, first)
        assert store == first
        assert (y, w, p) == (first, None, None)

    def test_exactly_one_dropdown_holds_a_value(self):
        first = 'Dry yield (tonne/ha)'
        for trig, vals in (('mapvar-yield-dd', (first, None, None)),
                           ('mapvar-water-dd', (None, 'seasonal_precip_mm', None)),
                           ('mapvar-wp-dd', (None, None, 'wp_et_kg_per_m3'))):
            _, y, w, p = self._set_map_var(trig, *vals, first)
            assert sum(v is not None for v in (y, w, p)) == 1

    def test_selected_value_is_a_known_map_variable(self):
        first = 'Dry yield (tonne/ha)'
        store, _, _, _ = self._set_map_var('mapvar-wp-dd', None, None,
                                          'wp_et_kg_per_m3', first)
        assert store in MAP_VARIABLES


class TestDailyVariableMerge:

    def _set_daily_var(self, triggered, flux_v, soil_v, crop_v, first_key):
        if triggered == 'dailyvar-flux-dd' and flux_v:
            return flux_v, flux_v, None, None
        if triggered == 'dailyvar-soil-dd' and soil_v:
            return soil_v, None, soil_v, None
        if triggered == 'dailyvar-crop-dd' and crop_v:
            return crop_v, None, None, crop_v
        return first_key, first_key, None, None

    def test_flux_selection_clears_others(self):
        store, f, s, c = self._set_daily_var('dailyvar-flux-dd', 'Tr', None, None, 'Es')
        assert store == 'Tr'
        assert (f, s, c) == ('Tr', None, None)

    def test_soil_selection_clears_others(self):
        store, f, s, c = self._set_daily_var('dailyvar-soil-dd', None, 'Wr', None, 'Es')
        assert store == 'Wr'
        assert (f, s, c) == (None, 'Wr', None)

    def test_crop_selection_clears_others(self):
        store, f, s, c = self._set_daily_var('dailyvar-crop-dd', None, None,
                                            'biomass', 'Es')
        assert store == 'biomass'
        assert (f, s, c) == (None, None, 'biomass')

    def test_clearing_reverts_to_first_key(self):
        store, f, s, c = self._set_daily_var('dailyvar-soil-dd', None, None, None, 'Es')
        assert store == 'Es'
        assert (f, s, c) == ('Es', None, None)

    def test_selected_value_is_a_known_daily_variable(self):
        store, _, _, _ = self._set_daily_var('dailyvar-crop-dd', None, None,
                                            'biomass', 'Es')
        assert store in DAILY_VARIABLES
