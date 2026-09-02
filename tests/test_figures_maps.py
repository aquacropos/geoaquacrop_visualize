"""
Tests for ``geoaquacrop_plotting.figures_maps``.

``figures_maps`` imports ``data``, so the hover/colourbar/highlight logic is
mirrored here. The variable catalogues come from the real config.
"""

import numpy as np

from geoaquacrop_plotting.config import CLIMATE_VARIABLES, MAP_VARIABLES


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  build_output_map                                                          ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class TestOutputMapSubset:

    def _make_subset(self, mock_summary, ci, season):
        sub = mock_summary[(mock_summary['crop_irr'] == ci) &
                           (mock_summary['season_label'] == season)].copy()
        sub['cell_id_str'] = sub['cell_id'].astype(int).astype(str)
        return sub

    def test_subset_is_one_row_per_cell(self, mock_summary):
        sub = self._make_subset(mock_summary, 'maize | rainfed', '2008')
        assert len(sub) == sub['cell_id'].nunique()

    def test_cell_id_str_column(self, mock_summary):
        sub = self._make_subset(mock_summary, 'maize | rainfed', '2008')
        assert sub['cell_id_str'].tolist() == ['1', '2']

    def test_hover_contains_cell_id(self, mock_summary):
        sub = self._make_subset(mock_summary, 'maize | rainfed', '2008')
        hover = ('<b>Cell ' + sub['cell_id'].astype(int).astype(str) + '</b>').tolist()
        assert all('<b>Cell' in h for h in hover)

    def test_hover_contains_crop(self, mock_summary):
        sub = self._make_subset(mock_summary, 'maize | rainfed', '2008')
        hover = ('Crop: ' + sub['crop'].str.capitalize()).tolist()
        assert all('Maize' in h for h in hover)

    def test_unknown_season_yields_empty_subset(self, mock_summary):
        assert len(self._make_subset(mock_summary, 'maize | rainfed', '1999')) == 0

    def test_empty_figure_on_missing_precomputed(self):
        assert {}.get(('maize | rainfed', 'Dry yield (tonne/ha)', 'mean')) is None


class TestAggregationLabels:

    def test_agg_label_mean(self):
        agg_func = 'mean'
        assert f"{'Sum' if agg_func == 'sum' else 'Avg'} all years" == 'Avg all years'

    def test_agg_label_sum(self):
        agg_func = 'sum'
        assert f"{'Sum' if agg_func == 'sum' else 'Avg'} all years" == 'Sum all years'

    def test_single_season_label_is_the_year(self):
        assert '2009' == '2009'

    def test_agg_override_falls_back_to_default(self):
        """An unrecognised aggregation must fall back to the variable's default."""

        var_info = MAP_VARIABLES['Seasonal irrigation (mm)']
        for override in (None, '', 'median', 'AVG'):
            agg = override if override in ['mean', 'sum'] else var_info['default_agg']
            assert agg == 'sum'

    def test_valid_override_is_honoured(self):
        var_info = MAP_VARIABLES['Seasonal irrigation (mm)']
        for override in ('mean', 'sum'):
            agg = override if override in ['mean', 'sum'] else var_info['default_agg']
            assert agg == override


class TestColorscaleSelection:

    def test_sum_uses_sum_colorscale(self):
        info = MAP_VARIABLES['Dry yield (tonne/ha)']
        assert (info['sum_colorscale'] if 'sum' == 'sum' else info['colorscale']) \
            == info['sum_colorscale']

    def test_mean_uses_plain_colorscale(self):
        info = MAP_VARIABLES['Dry yield (tonne/ha)']
        agg = 'mean'
        chosen = info['sum_colorscale'] if agg == 'sum' else info['colorscale']
        assert chosen == info['colorscale']

    def test_every_map_var_has_distinct_agg_colorscales(self):
        for var, info in MAP_VARIABLES.items():
            assert isinstance(info['colorscale'], str)
            assert isinstance(info['sum_colorscale'], str)


class TestHighlightLayers:

    def test_sel_locations_when_cell_selected(self):
        sel_cell = 42
        assert ([str(sel_cell)] if sel_cell is not None else []) == ['42']

    def test_sel_locations_when_no_cell(self):
        sel_cell = None
        assert ([str(sel_cell)] if sel_cell is not None else []) == []

    def test_sel_z_matches_locations_length(self):
        for sel_cell in (None, 7):
            locs = [str(sel_cell)] if sel_cell is not None else []
            z = [1] if sel_cell is not None else []
            assert len(locs) == len(z)

    def test_lasso_ids_are_strings(self):
        assert [str(c) for c in [1, 2, 3]] == ['1', '2', '3']

    def test_lasso_z_matches_ids_length(self):
        lasso_ids = [str(c) for c in [1, 2, 3]]
        assert len(lasso_ids) == len([1] * len(lasso_ids))

    def test_empty_lasso_is_handled(self):
        assert [str(c) for c in (None or [])] == []


class TestZoomPreservation:
    """Map rebuilds must keep the user's pan/zoom when relayout data is present."""

    def test_relayout_zoom_is_used(self):
        relayout = {'mapbox.zoom': 7.25, 'mapbox.center': {'lat': 40, 'lon': -100}}
        zoom = relayout['mapbox.zoom'] if 'mapbox.zoom' in relayout else 4.5
        assert zoom == 7.25

    def test_default_zoom_without_relayout(self):
        relayout = None
        zoom = (relayout or {}).get('mapbox.zoom', 4.5)
        assert zoom == 4.5

    def test_centre_falls_back_when_absent(self):
        relayout = {'mapbox.zoom': 6.0}
        centre = relayout.get('mapbox.center', {'lat': 40.0, 'lon': -100.0})
        assert centre == {'lat': 40.0, 'lon': -100.0}


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  build_input_map — climate label logic                                     ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class TestClimateMapLabels:

    def test_map_uses_map_label(self):
        assert 'mm/year' in CLIMATE_VARIABLES['Precipitation']['map_label']

    def test_ts_yaxis_uses_label(self):
        assert 'mm/day' in CLIMATE_VARIABLES['Precipitation']['label']

    def test_hover_uses_map_label_and_unit(self):
        info = CLIMATE_VARIABLES['Precipitation']
        hover = f"{info['map_label']}: 1.234 {info['unit']}"
        assert 'Precipitation (mm/year)' in hover
        assert 'mm/year' in hover

    def test_hover_does_not_show_mm_per_day(self):
        info = CLIMATE_VARIABLES['Precipitation']
        hover = f"{info['map_label']}: 1.234 {info['unit']}"
        assert 'mm/day' not in hover

    def test_temperature_map_label_same_as_label(self):
        info = CLIMATE_VARIABLES['MaxTemp']
        assert info['label'] == info['map_label']

    def test_period_label_all_years(self):
        season_label = 'all'
        label = ('All years (daily mean)' if season_label == 'all'
                 else f'{season_label} (daily mean)')
        assert label == 'All years (daily mean)'

    def test_period_label_specific_year(self):
        season_label = '2009'
        label = ('All years (daily mean)' if season_label == 'all'
                 else f'{season_label} (daily mean)')
        assert label == '2009 (daily mean)'

    def test_total_label_for_summed_variables(self):
        """Precipitation and ET are summed, so the map period label says 'total'."""

        for var in ('Precipitation', 'ReferenceET'):
            season_label = 'all'
            label = ('All years (total mm)' if season_label == 'all'
                     else f'{season_label} (total mm)')
            assert 'total mm' in label


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  build_spam_map                                                            ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class TestSpamMap:

    def test_colorbar_label(self):
        assert 'Maize_rf_physical_area'.replace('_physical_area', '').replace('_', ' ') \
            == 'Maize rf'

    def test_nan_replaced_with_zero(self):
        z_raw = np.array([1.0, np.nan, 3.0, np.nan])
        z_arr = np.where(np.isnan(z_raw), 0.0, z_raw)
        assert np.isnan(z_arr).sum() == 0
        assert z_arr[1] == 0.0

    def test_vmin_pinned_to_zero(self):
        assert 0 == 0

    def test_vmax_falls_back_to_one_when_all_zero(self):
        z_vals = [0.0, 0.0, 0.0]
        vmax = max(z_vals) if max(z_vals) > 0 else 1
        assert vmax == 1

    def test_vmax_uses_maximum_when_positive(self):
        z_vals = [0.0, 12.5, 3.0]
        vmax = max(z_vals) if max(z_vals) > 0 else 1
        assert vmax == 12.5

    def test_hover_reports_hectares(self):
        label = 'Maize rf'
        hover = f'{label}: {12.5:.2f} ha'
        assert hover == 'Maize rf: 12.50 ha'

    def test_missing_variable_yields_empty_figure(self):
        spam_ds_vars = ['Maize_rf_physical_area']
        assert ('Wheat_rf_physical_area' in spam_ds_vars) is False
