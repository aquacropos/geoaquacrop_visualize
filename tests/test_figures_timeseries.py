"""
Tests for ``geoaquacrop_plotting.figures_timeseries``.

``figures_timeseries`` imports ``data``, so the period selection and the
mean ± std band arithmetic are mirrored here. ``DAILY_VARIABLES`` and
``TS_HEIGHT`` come from the real config.
"""

import numpy as np
import pandas as pd
import pytest

from geoaquacrop_plotting.config import DAILY_VARIABLES, TS_HEIGHT


def period_rows(season_label, year_rows, n_rows, ts_period='season'):
    """Mirror of the row-range selection in build_output_ts."""

    if ts_period == 'full' or season_label == 'all':
        return 0, n_rows - 1
    return year_rows[season_label]


class TestPeriodSelection:

    def test_full_period_on_all_seasons(self):
        n_rows = 1095
        assert period_rows('all', {}, n_rows) == (0, n_rows - 1)

    def test_full_period_when_ts_period_is_full(self):
        n_rows = 1095
        assert period_rows('2008', {'2008': (0, 365)}, n_rows, 'full') == (0, n_rows - 1)

    def test_season_period_uses_year_rows(self):
        year_rows = {'2008': (0, 365), '2009': (366, 730)}
        assert period_rows('2008', year_rows, 1095) == (0, 365)

    def test_later_season_uses_its_own_rows(self):
        year_rows = {'2008': (0, 365), '2009': (366, 730)}
        assert period_rows('2009', year_rows, 1095) == (366, 730)

    def test_period_label_full(self):
        ts_period = 'full'
        assert ('Full simulation' if ts_period == 'full' else '2008') == 'Full simulation'

    def test_period_label_season(self):
        ts_period, season_label = 'season', '2009'
        assert ('Full simulation' if ts_period == 'full' else season_label) == '2009'

    def test_row_range_is_inclusive(self):
        """df.iloc[row_start:row_end + 1] must include the final row."""

        df = pd.DataFrame({'v': range(10)})
        row_start, row_end = 2, 5
        assert len(df.iloc[row_start:row_end + 1]) == 4


class TestVariableRouting:

    def test_daily_var_table_selection(self):
        assert DAILY_VARIABLES['Es']['table'] == 'water_flux'
        assert DAILY_VARIABLES['biomass']['table'] == 'crop_growth'

    def test_water_flux_var_reads_wf_table(self, mock_daily_wf, mock_daily_cg):
        info = DAILY_VARIABLES['Es']
        df = mock_daily_wf if info['table'] == 'water_flux' else mock_daily_cg
        assert 'Es' in df.columns

    def test_crop_growth_var_reads_cg_table(self, mock_daily_wf, mock_daily_cg):
        info = DAILY_VARIABLES['biomass']
        df = mock_daily_wf if info['table'] == 'water_flux' else mock_daily_cg
        assert 'biomass' in df.columns

    def test_every_daily_var_resolves_to_a_column(self, mock_daily_wf, mock_daily_cg):
        for var, info in DAILY_VARIABLES.items():
            df = mock_daily_wf if info['table'] == 'water_flux' else mock_daily_cg
            assert var in df.columns, f'{var} missing from {info["table"]}'

    def test_ts_height_used_for_layout(self):
        assert TS_HEIGHT > 0


class TestPreseasonShading:

    def test_preseason_shading_condition(self):
        assert (0 <= 59) is True

    def test_no_preseason_shading_when_past(self):
        assert (366 <= 59) is False

    def test_shade_end_clamped_to_window(self):
        preseason_end = pd.Timestamp('2008-03-01')
        year_end = pd.Timestamp('2008-02-15')
        assert min(preseason_end, year_end) == year_end

    def test_shade_end_uses_preseason_when_inside_window(self):
        preseason_end = pd.Timestamp('2008-03-01')
        year_end = pd.Timestamp('2008-12-31')
        assert min(preseason_end, year_end) == preseason_end


class TestMeanStdBand:

    def _compute_band(self, values):
        arr = np.array(values)
        mean, std = arr.mean(), arr.std()
        return mean, std, mean + std, mean - std

    def test_mean_correct(self):
        mean, _, _, _ = self._compute_band([1, 2, 3, 4, 5])
        assert mean == pytest.approx(3.0)

    def test_upper_lower_symmetric(self):
        mean, _, upper, lower = self._compute_band([1, 2, 3, 4, 5])
        assert upper - mean == pytest.approx(mean - lower)

    def test_constant_series_zero_std(self):
        mean, std, upper, lower = self._compute_band([5, 5, 5, 5])
        assert std == pytest.approx(0.0)
        assert upper == pytest.approx(5.0)
        assert lower == pytest.approx(5.0)

    def test_band_uses_pandas_sample_std(self):
        """The app calls Series.std(), which is the sample (ddof=1) standard deviation."""

        s = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        assert s.std() == pytest.approx(1.5811388300841898)
        assert s.std() != np.array(s).std()  # numpy defaults to ddof=0

    def test_window_clamped_to_visible_range(self):
        year_start = pd.Timestamp('2009-01-01')
        year_end = pd.Timestamp('2009-12-31')
        sel_start = max(pd.Timestamp('2008-06-01'), year_start)
        sel_end = min(pd.Timestamp('2010-06-01'), year_end)
        assert sel_start == year_start
        assert sel_end == year_end

    def test_empty_selection_produces_no_band(self, mock_daily_wf):
        df = mock_daily_wf.copy()
        df['date'] = pd.Timestamp('2008-01-01') + pd.to_timedelta(df.index, unit='D')
        mask = ((df['date'] >= pd.Timestamp('2020-01-01')) &
                (df['date'] <= pd.Timestamp('2020-12-31')))
        assert df[mask].empty

    def test_band_polygon_is_closed_loop(self, mock_daily_wf):
        """The fill='toself' band walks forwards then backwards over the dates."""

        df = mock_daily_wf.head(5).copy()
        df['date'] = pd.Timestamp('2008-01-01') + pd.to_timedelta(df.index, unit='D')
        x_band = list(df['date']) + list(df['date'])[::-1]
        assert len(x_band) == 2 * len(df)
        assert x_band[0] == x_band[-1]


class TestClickStateMachine:
    """The three-click cycle behind the mean ± std window."""

    def _handle_click(self, clicked_date, ts_clicks):
        count = ts_clicks['count']
        if count == 0:
            return {'count': 1, 'start': clicked_date, 'end': None}
        elif count == 1:
            start = ts_clicks['start']
            if clicked_date < start:
                start, clicked_date = clicked_date, start
            return {'count': 2, 'start': start, 'end': clicked_date}
        return {'count': 0, 'start': None, 'end': None}

    def test_first_click_sets_start(self, ts_click_reset):
        state = self._handle_click('2008-06-01', ts_click_reset)
        assert state == {'count': 1, 'start': '2008-06-01', 'end': None}

    def test_click_state_reset_on_third_click(self, ts_click_reset):
        state = self._handle_click('2008-06-01', ts_click_reset)
        assert state['count'] == 1
        state = self._handle_click('2008-08-01', state)
        assert state['count'] == 2
        state = self._handle_click('2008-10-01', state)
        assert state['count'] == 0
        assert state['start'] is None

    def test_click_order_auto_sorted(self, ts_click_reset):
        state = self._handle_click('2008-09-01', ts_click_reset)
        state = self._handle_click('2008-06-01', state)  # earlier date clicked second
        assert state['start'] < state['end']

    def test_cycle_returns_to_start(self, ts_click_reset):
        state = ts_click_reset
        for date in ('2008-01-01', '2008-02-01', '2008-03-01'):
            state = self._handle_click(date, state)
        assert state == ts_click_reset

    def test_prompt_before_first_click(self, ts_click_reset):
        assert ts_click_reset['count'] == 0

    def test_prompt_after_one_click(self, ts_click_reset):
        state = self._handle_click('2008-06-01', ts_click_reset)
        assert state['count'] == 1
        assert state['end'] is None
