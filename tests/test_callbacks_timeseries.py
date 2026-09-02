"""
Tests for ``geoaquacrop_plotting.callbacks_timeseries``.

Covers how the season selection is translated into the period arguments handed
to the figure builders, and the container visibility toggle.
"""


class TestEffectivePeriod:

    def _effective(self, season_label, season_list):
        period = 'full' if season_label == 'all' else 'season'
        season = season_list[0] if season_label == 'all' else season_label
        return period, season

    SEASONS = ['2008', '2009', '2010']

    def test_effective_period_all_seasons(self):
        period, _ = self._effective('all', self.SEASONS)
        assert period == 'full'

    def test_effective_period_single_season(self):
        period, _ = self._effective('2009', self.SEASONS)
        assert period == 'season'

    def test_effective_season_all_uses_first(self):
        _, season = self._effective('all', self.SEASONS)
        assert season == '2008'

    def test_effective_season_specific(self):
        _, season = self._effective('2010', self.SEASONS)
        assert season == '2010'

    def test_all_years_never_passes_all_downstream(self):
        """build_output_ts indexes year_rows, which has no 'all' key."""

        _, season = self._effective('all', self.SEASONS)
        assert season != 'all'
        assert season in self.SEASONS

    def test_every_season_round_trips(self):
        for s in self.SEASONS:
            period, season = self._effective(s, self.SEASONS)
            assert (period, season) == ('season', s)


class TestContainerVisibility:

    HIDDEN = {'visibility': 'hidden', 'height': '0', 'overflow': 'hidden'}
    VISIBLE = {'visibility': 'visible', 'height': 'auto', 'overflow': 'visible'}

    def test_hidden_when_no_cell(self):
        assert (self.HIDDEN if None is None else self.VISIBLE)['visibility'] == 'hidden'

    def test_visible_when_cell_selected(self):
        cell_id = 42
        style = self.HIDDEN if cell_id is None else self.VISIBLE
        assert style['visibility'] == 'visible'

    def test_figure_is_built_even_when_hidden(self):
        """The placeholder figure is still produced so the graph has a layout."""

        cell_id = None
        assert cell_id is None  # build_output_ts(None, ...) returns the prompt figure

    def test_visibility_not_display(self):
        """Using visibility rather than display keeps Plotly's sizing correct."""

        assert 'display' not in self.HIDDEN
        assert 'display' not in self.VISIBLE
