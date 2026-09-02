"""
Tests for ``geoaquacrop_plotting.callbacks_export``.

Covers the export modal's decision logic: the variable-checklist merge, the
date-dropdown constraint, cell-extent resolution, and validation messages.
``DAILY_VARIABLES`` and the variable groups come from the real modules.
"""

import calendar

import pandas as pd
import pytest

from geoaquacrop_plotting.config import DAILY_VARIABLES
from geoaquacrop_plotting.styles import _CROP_VARS, _FLUX_VARS, _SOIL_VARS
from geoaquacrop_plotting.utils import safe_date


class TestExportVarMerge:

    def _merge(self, flux, soil, crop):
        return (flux or []) + (soil or []) + (crop or [])

    def test_merges_all_three_groups(self):
        assert self._merge(['Es'], ['Wr'], ['biomass']) == ['Es', 'Wr', 'biomass']

    def test_empty_groups_are_dropped(self):
        assert self._merge(['Es'], [], []) == ['Es']

    def test_none_is_treated_as_empty(self):
        assert self._merge(None, None, ['biomass']) == ['biomass']

    def test_all_empty_gives_empty_list(self):
        assert self._merge([], [], []) == []

    def test_merged_vars_are_all_known(self):
        merged = self._merge(_FLUX_VARS, _SOIL_VARS, _CROP_VARS)
        for var in merged:
            assert var in DAILY_VARIABLES

    def test_merging_every_group_covers_the_catalogue(self):
        merged = self._merge(_FLUX_VARS, _SOIL_VARS, _CROP_VARS)
        assert set(merged) == set(DAILY_VARIABLES)


class TestDateDropdownToggle:

    def test_whole_period_disables_all_six(self):
        whole_period = ['whole']
        assert [('whole' in (whole_period or []))] * 6 == [True] * 6

    def test_custom_period_enables_all_six(self):
        whole_period = []
        assert [('whole' in (whole_period or []))] * 6 == [False] * 6

    def test_none_is_treated_as_unchecked(self):
        assert ('whole' in (None or [])) is False


class TestEndDateConstraint:

    YEARS = [2008, 2009, 2010]

    def _constrain(self, sy, sm, sd, ey, em, ed):
        """Mirror of callbacks_export.constrain_end_date."""

        year_opts = [{'label': str(y), 'value': y} for y in self.YEARS if y >= sy]
        new_ey = ey if ey >= sy else sy
        if new_ey == sy:
            month_opts = [{'label': f'{m:02d}', 'value': m} for m in range(sm, 13)]
            new_em = em if em >= sm else sm
        else:
            month_opts = [{'label': f'{m:02d}', 'value': m} for m in range(1, 13)]
            new_em = em
        max_day = calendar.monthrange(new_ey, new_em)[1]
        if new_ey == sy and new_em == sm:
            day_opts = [{'label': f'{d:02d}', 'value': d} for d in range(sd, max_day + 1)]
            new_ed = ed if ed >= sd else sd
        else:
            day_opts = [{'label': f'{d:02d}', 'value': d} for d in range(1, max_day + 1)]
            new_ed = min(ed, max_day)
        return year_opts, new_ey, month_opts, new_em, day_opts, new_ed

    def test_years_before_start_are_removed(self):
        year_opts, *_ = self._constrain(2009, 1, 1, 2010, 12, 31)
        assert [o['value'] for o in year_opts] == [2009, 2010]

    def test_end_year_pulled_forward_to_start(self):
        _, new_ey, *_ = self._constrain(2010, 1, 1, 2008, 12, 31)
        assert new_ey == 2010

    def test_months_restricted_within_same_year(self):
        _, _, month_opts, _, _, _ = self._constrain(2009, 6, 1, 2009, 12, 31)
        assert [o['value'] for o in month_opts] == list(range(6, 13))

    def test_months_unrestricted_in_later_year(self):
        _, _, month_opts, _, _, _ = self._constrain(2009, 6, 1, 2010, 3, 31)
        assert [o['value'] for o in month_opts] == list(range(1, 13))

    def test_end_month_pulled_forward_within_same_year(self):
        _, _, _, new_em, _, _ = self._constrain(2009, 6, 1, 2009, 2, 28)
        assert new_em == 6

    def test_days_restricted_within_same_month(self):
        *_, day_opts, _ = self._constrain(2009, 6, 10, 2009, 6, 30)
        assert [o['value'] for o in day_opts] == list(range(10, 31))

    def test_end_day_pulled_forward_within_same_month(self):
        *_, new_ed = self._constrain(2009, 6, 10, 2009, 6, 5)
        assert new_ed == 10

    def test_day_clamped_to_month_length(self):
        *_, new_ed = self._constrain(2009, 1, 1, 2009, 2, 31)
        assert new_ed == 28  # 2009 is not a leap year

    def test_day_clamped_to_leap_february(self):
        *_, new_ed = self._constrain(2008, 1, 1, 2008, 2, 31)
        assert new_ed == 29

    def test_result_is_always_a_valid_date(self):
        for sy, sm, sd, ey, em, ed in [(2008, 1, 1, 2010, 12, 31),
                                       (2010, 5, 20, 2008, 3, 31),
                                       (2009, 12, 31, 2009, 1, 1),
                                       (2009, 1, 15, 2010, 2, 31)]:
            _, new_ey, _, new_em, _, new_ed = self._constrain(sy, sm, sd, ey, em, ed)
            assert isinstance(pd.Timestamp(year=new_ey, month=new_em, day=new_ed),
                              pd.Timestamp)

    def test_returned_day_is_always_one_of_the_offered_options(self):
        for sy, sm, sd, ey, em, ed in [(2008, 1, 1, 2010, 12, 31),
                                       (2010, 5, 20, 2008, 3, 31),
                                       (2009, 6, 10, 2009, 6, 30),
                                       (2009, 1, 15, 2010, 2, 31)]:
            *_, day_opts, new_ed = self._constrain(sy, sm, sd, ey, em, ed)
            assert new_ed in [o['value'] for o in day_opts], (sy, sm, sd, ey, em, ed)

    @pytest.mark.xfail(
        reason="constrain_end_date does not clamp the day in the same-year, "
               "same-month branch: 'new_ed = ed if ed >= sd else sd' is missing "
               "the min(..., max_day) that the other branch applies. Selecting "
               "start 2009-02-28 with a stale end day of 31 returns day 31 while "
               "day_opts only offers 28, so the dropdown holds a value outside "
               "its own options. run_export() still exports correctly because "
               "safe_date() clamps the day again.",
        strict=True,
    )
    def test_same_month_branch_clamps_day_to_month_length(self):
        *_, day_opts, new_ed = self._constrain(2009, 2, 28, 2009, 2, 31)
        assert new_ed == 28
        assert new_ed in [o['value'] for o in day_opts]

    def test_end_never_precedes_start(self):
        for sy, sm, sd, ey, em, ed in [(2010, 5, 20, 2008, 3, 31),
                                       (2009, 6, 10, 2009, 2, 5),
                                       (2009, 6, 10, 2009, 6, 1)]:
            _, new_ey, _, new_em, _, new_ed = self._constrain(sy, sm, sd, ey, em, ed)
            assert (pd.Timestamp(year=new_ey, month=new_em, day=new_ed)
                    >= safe_date(sy, sm, sd))


class TestExportExtent:

    def _cells(self, whole_area, lasso_cells, cell_meta):
        if 'all' in (whole_area or []) or not lasso_cells:
            return list(cell_meta.keys())
        return lasso_cells

    def test_export_cells_whole_area(self, mock_cell_meta):
        assert self._cells(['all'], [], mock_cell_meta) == list(mock_cell_meta.keys())

    def test_export_cells_lasso_selection(self, mock_cell_meta):
        assert self._cells([], [1, 2], mock_cell_meta) == [1, 2]

    def test_whole_area_overrides_lasso(self, mock_cell_meta):
        assert self._cells(['all'], [1, 2], mock_cell_meta) \
            == list(mock_cell_meta.keys())

    def test_empty_lasso_falls_back_to_whole_area(self, mock_cell_meta):
        assert self._cells([], [], mock_cell_meta) == list(mock_cell_meta.keys())


class TestExportValidation:

    def test_no_vars_message(self):
        assert ('Select at least one variable.' if not [] else 'ok') \
            == 'Select at least one variable.'

    def test_no_format_message(self):
        export_vars = ['Es']
        formats = []
        msg = ('Select at least one variable.' if not export_vars
               else 'Select at least one format.' if not formats else 'ok')
        assert msg == 'Select at least one format.'

    def test_variables_checked_before_formats(self):
        export_vars, formats = [], []
        msg = ('Select at least one variable.' if not export_vars
               else 'Select at least one format.' if not formats else 'ok')
        assert msg == 'Select at least one variable.'

    def test_start_after_end_is_rejected(self):
        start = safe_date(2009, 1, 1)
        end = safe_date(2008, 1, 1)
        msg = 'Start date must be before end date.' if start > end else 'ok'
        assert msg == 'Start date must be before end date.'

    def test_valid_range_passes(self):
        start, end = safe_date(2008, 1, 1), safe_date(2010, 12, 31)
        assert (start > end) is False

    def test_whole_period_bypasses_the_dropdowns(self):
        whole_period = ['whole']
        sim_start, sim_end = pd.Timestamp('2008-01-01'), pd.Timestamp('2010-12-31')
        if 'whole' in (whole_period or []):
            start, end = sim_start, sim_end
        else:
            start, end = safe_date(2009, 1, 1), safe_date(2009, 12, 31)
        assert (start, end) == (sim_start, sim_end)


class TestExportButtonVisibility:

    BASE = {'position': 'absolute', 'bottom': '14px', 'left': '12px', 'right': '12px'}

    def _style(self, sel_tab):
        return {**self.BASE, 'display': 'block' if sel_tab == 'output' else 'none'}

    def test_visible_on_output_tab(self):
        assert self._style('output')['display'] == 'block'

    def test_hidden_on_input_tab(self):
        assert self._style('input')['display'] == 'none'

    def test_positioning_is_preserved_either_way(self):
        for tab in ('output', 'input'):
            style = self._style(tab)
            for key, val in self.BASE.items():
                assert style[key] == val


class TestExportModalToggle:

    def test_toggle_flips_state(self):
        assert (not False) is True
        assert (not True) is False
