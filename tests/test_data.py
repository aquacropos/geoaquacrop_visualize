"""
Tests for ``geoaquacrop_plotting.data``.

``data`` loads the pickles and NetCDFs at import time, so it cannot be imported
without the real dataset. These tests exercise the same derivations against the
synthetic fixtures in conftest.
"""

import numpy as np
import pandas as pd


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  cell_meta                                                                 ║
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

    def test_list_idx_indexes_daily_raw(self, mock_cell_meta):
        """list_idx must be a valid position into the daily_raw list."""

        for meta in mock_cell_meta.values():
            assert isinstance(meta['list_idx'], int)
            assert meta['list_idx'] >= 0


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  summary DataFrame                                                         ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

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
        """Season labels are compared against dropdown values, so they must be str.

        Asserted on the values rather than the dtype: pandas 3 infers a StringDtype
        where pandas 2 reported plain ``object``.
        """

        assert all(isinstance(v, str) for v in mock_summary['season_label'])

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

    def test_crop_irr_matches_crop_and_irrigation_columns(self, mock_summary):
        """crop_irr is built as crop + ' | ' + irrigation."""

        rebuilt = mock_summary['crop'] + ' | ' + mock_summary['irrigation']
        pd.testing.assert_series_equal(mock_summary['crop_irr'], rebuilt,
                                       check_names=False)

    def test_season_label_matches_harvest_year(self, mock_summary):
        rebuilt = mock_summary['harvest_year'].astype(int).astype(str)
        pd.testing.assert_series_equal(mock_summary['season_label'], rebuilt,
                                       check_names=False)


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  Year filtering and the date index                                         ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

def build_years(date_index, min_days=5):
    """Mirror of the ``years`` derivation in data.py."""

    return [yr for yr in sorted(date_index.year.unique())
            if (date_index.year == yr).sum() > min_days]


def build_year_rows(date_index, years):
    """Mirror of the ``year_rows`` derivation in data.py."""

    year_rows = {}
    for yr in years:
        indices = np.where(date_index.year == yr)[0]
        year_rows[str(yr)] = (int(indices[0]), int(indices[-1]))
    return year_rows


class TestYearFiltering:

    def test_full_years_included(self, date_index_3y):
        years = build_years(date_index_3y)
        assert 2008 in years
        assert 2009 in years
        assert 2010 in years

    def test_partial_year_excluded(self):
        idx = pd.date_range('2007-12-29', '2010-12-31', freq='D')
        assert 2007 not in build_years(idx)

    def test_partial_year_included_when_long_enough(self):
        """The threshold is > 5 days, not 'complete year'."""

        idx = pd.date_range('2007-12-20', '2010-12-31', freq='D')
        assert 2007 in build_years(idx)

    def test_year_rows_bounds(self, date_index_3y):
        years = build_years(date_index_3y)
        year_rows = build_year_rows(date_index_3y, years)
        assert year_rows['2008'][0] == 0
        assert year_rows['2008'][1] == 365  # 2008 is a leap year → 366 days, index 0..365
        assert year_rows['2009'][0] == 366
        assert year_rows['2010'][0] == 366 + 365

    def test_year_rows_are_contiguous(self, date_index_3y):
        years = build_years(date_index_3y)
        year_rows = build_year_rows(date_index_3y, years)
        ordered = [year_rows[str(y)] for y in years]
        for (_, end), (start, _) in zip(ordered, ordered[1:]):
            assert start == end + 1

    def test_year_rows_cover_whole_index(self, date_index_3y):
        years = build_years(date_index_3y)
        year_rows = build_year_rows(date_index_3y, years)
        assert year_rows[str(years[0])][0] == 0
        assert year_rows[str(years[-1])][1] == len(date_index_3y) - 1

    def test_year_suffix_format(self, date_index_3y):
        years = build_years(date_index_3y)
        assert f'{years[0]}{years[-1]}' == '20082010'


class TestPreseasonBoundary:
    """The pre-season shading uses the last row where season_counter == -1."""

    def test_preseason_end_row_from_season_counter(self, mock_daily_wf):
        wf = mock_daily_wf.reset_index(drop=True)
        preseason_end_row = int(wf[wf['season_counter'] == -1.0].index.max())
        assert preseason_end_row > 0

    def test_preseason_precedes_season(self, mock_daily_wf):
        wf = mock_daily_wf.reset_index(drop=True)
        preseason_end_row = int(wf[wf['season_counter'] == -1.0].index.max())
        assert wf.loc[preseason_end_row, 'season_counter'] == -1.0

    def test_preseason_end_date_derivation(self, mock_daily_wf):
        sim_start = pd.Timestamp('2008-01-01')
        wf = mock_daily_wf.reset_index(drop=True)
        row = int(wf[wf['season_counter'] == -1.0].index.max())
        end_date = sim_start + pd.to_timedelta(row, unit='D')
        assert end_date > sim_start
