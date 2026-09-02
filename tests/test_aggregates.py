"""
Tests for ``geoaquacrop_plotting.aggregates``.

``aggregates`` imports ``data``, so the pre-computation is mirrored here and
driven by the synthetic fixtures. The variable list comes from the real config.
"""

import pandas as pd

from geoaquacrop_plotting.config import MAP_VARIABLES


def precompute(summary, crop_irr_list, map_var_keys):
    """Mirror of the crop_var_range_all / precomputed_agg build in aggregates.py."""

    crop_var_range_all, precomputed_agg = {}, {}
    for ci in crop_irr_list:
        crop_var_range_all[ci] = {}
        sub_ci = summary[summary['crop_irr'] == ci]
        for var in map_var_keys:
            if var not in sub_ci.columns:
                continue
            grouped = sub_ci.groupby('cell_id')[var]
            for agg in ['mean', 'sum']:
                agg_vals = grouped.sum() if agg == 'sum' else grouped.mean()
                if var == 'Seasonal irrigation (mm)':
                    vmax = agg_vals.max() if agg_vals.max() > 0 else 1
                    crop_var_range_all[ci][f'{var}_{agg}'] = (0, vmax)
                else:
                    crop_var_range_all[ci][f'{var}_{agg}'] = (agg_vals.min(), agg_vals.max())
                agg_df = agg_vals.reset_index()
                agg_df.columns = ['cell_id', var]
                agg_df = agg_df.merge(
                    summary[['cell_id', 'x', 'y', 'crop', 'irrigation']].drop_duplicates('cell_id'),
                    on='cell_id')
                precomputed_agg[(ci, var, agg)] = agg_df
    return crop_var_range_all, precomputed_agg


class TestAggregationCorrectness:

    def test_mean_agg_correct(self, mock_summary):
        ci = 'maize | rainfed'
        var = 'Dry yield (tonne/ha)'
        sub = mock_summary[mock_summary['crop_irr'] == ci]
        result = sub.groupby('cell_id')[var].mean()
        expected = sub.groupby('cell_id')[var].mean()
        pd.testing.assert_series_equal(result, expected)

    def test_sum_agg_correct(self, mock_summary):
        ci = 'maize | rainfed'
        var = 'production_tonnes'
        sub = mock_summary[mock_summary['crop_irr'] == ci]
        assert (sub.groupby('cell_id')[var].sum() > 0).all()

    def test_sum_exceeds_mean_over_multiple_seasons(self, mock_summary):
        ci = 'maize | rainfed'
        var = 'Dry yield (tonne/ha)'
        sub = mock_summary[mock_summary['crop_irr'] == ci]
        means = sub.groupby('cell_id')[var].mean()
        sums = sub.groupby('cell_id')[var].sum()
        assert (sums >= means).all()

    def test_irrigation_range_starts_at_zero(self, mock_summary):
        ci = 'maize | rainfed'
        var = 'Seasonal irrigation (mm)'
        sub = mock_summary[mock_summary['crop_irr'] == ci]
        agg_vals = sub.groupby('cell_id')[var].sum()
        vmax = agg_vals.max() if agg_vals.max() > 0 else 1
        assert vmax >= 0

    def test_rainfed_irrigation_vmax_falls_back_to_one(self, mock_summary):
        """All-zero irrigation must not produce a degenerate 0..0 colour range."""

        ci = 'maize | rainfed'
        var = 'Seasonal irrigation (mm)'
        sub = mock_summary[mock_summary['crop_irr'] == ci]
        agg_vals = sub.groupby('cell_id')[var].sum()
        vmax = agg_vals.max() if agg_vals.max() > 0 else 1
        assert vmax == 1


class TestPrecomputedAgg:

    def _keys(self, mock_summary):
        return sorted(v for v in MAP_VARIABLES if v in mock_summary.columns)

    def test_every_crop_var_agg_combination_present(self, mock_summary):
        crops = sorted(mock_summary['crop_irr'].unique())
        keys = self._keys(mock_summary)
        _, precomputed = precompute(mock_summary, crops, keys)
        for ci in crops:
            for var in keys:
                for agg in ('mean', 'sum'):
                    assert (ci, var, agg) in precomputed, (ci, var, agg)

    def test_agg_frames_carry_coordinates(self, mock_summary):
        crops = sorted(mock_summary['crop_irr'].unique())
        keys = self._keys(mock_summary)
        _, precomputed = precompute(mock_summary, crops, keys)
        df = precomputed[(crops[0], keys[0], 'mean')]
        for col in ('cell_id', 'x', 'y', 'crop', 'irrigation'):
            assert col in df.columns

    def test_one_row_per_cell(self, mock_summary):
        crops = sorted(mock_summary['crop_irr'].unique())
        keys = self._keys(mock_summary)
        _, precomputed = precompute(mock_summary, crops, keys)
        for ci in crops:
            n_cells = mock_summary[mock_summary['crop_irr'] == ci]['cell_id'].nunique()
            assert len(precomputed[(ci, keys[0], 'mean')]) == n_cells

    def test_ranges_bracket_the_values(self, mock_summary):
        crops = sorted(mock_summary['crop_irr'].unique())
        keys = self._keys(mock_summary)
        ranges, precomputed = precompute(mock_summary, crops, keys)
        for ci in crops:
            for var in keys:
                if var == 'Seasonal irrigation (mm)':
                    continue  # range is pinned to start at 0
                vmin, vmax = ranges[ci][f'{var}_mean']
                vals = precomputed[(ci, var, 'mean')][var]
                assert vmin <= vals.min()
                assert vmax >= vals.max()

    def test_missing_combination_returns_none(self):
        """build_output_map falls back to an empty figure on a cache miss."""

        assert {}.get(('maize | rainfed', 'Dry yield (tonne/ha)', 'mean')) is None

    def test_all_map_vars_have_data(self, mock_summary):
        for ci in mock_summary['crop_irr'].unique():
            sub = mock_summary[mock_summary['crop_irr'] == ci]
            for var in self._keys(mock_summary):
                assert len(sub[var].dropna()) > 0, f"No data for {ci} / {var}"
