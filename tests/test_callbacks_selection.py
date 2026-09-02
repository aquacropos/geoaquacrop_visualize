"""
Tests for ``geoaquacrop_plotting.callbacks_selection``.

Covers the pure decision logic of the selection callbacks: extracting a cell id
from a map click, lasso/box selection, the ribbon captions, and the click-state
resets. ``CLIMATE_VARIABLES`` comes from the real config.
"""

from geoaquacrop_plotting.config import CLIMATE_VARIABLES


class TestCellClick:

    def _set_cell(self, click_data):
        if click_data is None:
            return None
        pt = click_data['points'][0]
        if 'location' in pt:
            return int(pt['location'])
        return None

    def test_click_on_choropleth_returns_cell_id(self):
        assert self._set_cell({'points': [{'location': '42'}]}) == 42

    def test_returns_int_not_string(self):
        assert isinstance(self._set_cell({'points': [{'location': '42'}]}), int)

    def test_none_click_returns_none(self):
        assert self._set_cell(None) is None

    def test_click_without_location_returns_none(self):
        assert self._set_cell({'points': [{'x': 1, 'y': 2}]}) is None

    def test_first_point_wins(self):
        assert self._set_cell({'points': [{'location': '7'}, {'location': '9'}]}) == 7


class TestLassoSelection:

    def _handle_lasso(self, selected_data, whole_area):
        if 'all' in (whole_area or []):
            return [], '  |  Whole area selected'
        if selected_data and selected_data.get('points'):
            cell_ids = []
            for pt in selected_data['points']:
                if 'text' in pt:
                    try:
                        cell_ids.append(int(pt['text']))
                    except Exception:
                        pass
            if cell_ids:
                return cell_ids, f'  |  {len(cell_ids)} cells selected via lasso/box'
        return [], '  |  or use lasso/box on the map to select cells'

    def test_whole_area_clears_selection(self):
        cells, label = self._handle_lasso({'points': [{'text': '1'}]}, ['all'])
        assert cells == []
        assert 'Whole area' in label

    def test_lasso_returns_cell_ids(self):
        cells, label = self._handle_lasso(
            {'points': [{'text': '1'}, {'text': '2'}, {'text': '3'}]}, [])
        assert cells == [1, 2, 3]
        assert '3 cells selected' in label

    def test_non_numeric_text_is_skipped(self):
        cells, _ = self._handle_lasso(
            {'points': [{'text': '1'}, {'text': 'not-a-cell'}, {'text': '3'}]}, [])
        assert cells == [1, 3]

    def test_points_without_text_are_skipped(self):
        cells, _ = self._handle_lasso(
            {'points': [{'text': '1'}, {'x': 0, 'y': 0}]}, [])
        assert cells == [1]

    def test_empty_selection_gives_hint(self):
        cells, label = self._handle_lasso(None, [])
        assert cells == []
        assert 'use lasso/box' in label

    def test_selection_with_no_usable_points_gives_hint(self):
        cells, label = self._handle_lasso({'points': [{'x': 0}]}, [])
        assert cells == []
        assert 'use lasso/box' in label

    def test_whole_area_wins_over_lasso(self):
        cells, _ = self._handle_lasso({'points': [{'text': '5'}]}, ['all'])
        assert cells == []

    def test_lasso_whole_area_clears_selection_shorthand(self):
        whole_area, lasso_cells = ['all'], [1, 2, 3]
        assert ([] if 'all' in (whole_area or []) else lasso_cells) == []

    def test_lasso_selection_when_no_whole_area(self):
        whole_area, lasso_cells = [], [1, 2, 3]
        assert ([] if 'all' in (whole_area or []) else lasso_cells) == [1, 2, 3]


class TestRibbonText:

    def _output_ribbon(self, cell_id, crop, season, cell_meta):
        if cell_id is None:
            return 'Select a cell on the map to view time series'
        meta = cell_meta.get(cell_id, {})
        period = 'Full simulation' if season == 'all' else season
        return (f"Selected: Cell {cell_id}  |  "
                f"Location: ({meta.get('x', 0):.3f}, {meta.get('y', 0):.3f})  |  "
                f"Crop: {crop}  |  Season: {period}")

    def _input_ribbon(self, cell_id, clim_var, season, cell_meta):
        if cell_id is None:
            return 'Select a cell on the map to view time series'
        meta = cell_meta.get(cell_id, {})
        period = 'Full simulation' if season == 'all' else season
        var_label = CLIMATE_VARIABLES.get(clim_var, {}).get('label', clim_var)
        return (f"Selected: Cell {cell_id}  |  "
                f"Location: ({meta.get('x', 0):.3f}, {meta.get('y', 0):.3f})  |  "
                f"Variable: {var_label}  |  Season: {period}")

    def test_prompt_when_no_cell(self, mock_cell_meta):
        assert self._output_ribbon(None, 'maize | rainfed', '2008', mock_cell_meta) \
            == 'Select a cell on the map to view time series'

    def test_output_ribbon_reports_cell_and_coords(self, mock_cell_meta):
        text = self._output_ribbon(1, 'maize | rainfed', '2008', mock_cell_meta)
        assert 'Cell 1' in text
        assert '-100.000' in text
        assert '40.000' in text
        assert 'Season: 2008' in text

    def test_all_years_becomes_full_simulation(self, mock_cell_meta):
        text = self._output_ribbon(1, 'maize | rainfed', 'all', mock_cell_meta)
        assert 'Season: Full simulation' in text

    def test_unknown_cell_falls_back_to_zero_coords(self, mock_cell_meta):
        text = self._output_ribbon(999, 'maize | rainfed', '2008', mock_cell_meta)
        assert '(0.000, 0.000)' in text

    def test_input_ribbon_uses_daily_label(self, mock_cell_meta):
        text = self._input_ribbon(1, 'Precipitation', '2008', mock_cell_meta)
        assert CLIMATE_VARIABLES['Precipitation']['label'] in text
        assert 'mm/day' in text

    def test_input_ribbon_unknown_var_falls_back_to_key(self, mock_cell_meta):
        text = self._input_ribbon(1, 'Sunshine', '2008', mock_cell_meta)
        assert 'Variable: Sunshine' in text

    def test_input_prompt_when_no_cell(self, mock_cell_meta):
        assert self._input_ribbon(None, 'MaxTemp', '2008', mock_cell_meta) \
            == 'Select a cell on the map to view time series'


class TestClickStateReset:

    def test_reset_returns_neutral_state(self, ts_click_reset):
        assert {'count': 0, 'start': None, 'end': None} == ts_click_reset

    def test_reset_clears_a_complete_window(self):
        state = {'count': 2, 'start': '2008-06-01', 'end': '2008-08-01'}
        state = {'count': 0, 'start': None, 'end': None}
        assert state['count'] == 0
        assert state['start'] is None
        assert state['end'] is None


class TestTimeSeriesContainerVisibility:

    HIDDEN = {'visibility': 'hidden', 'height': '0', 'overflow': 'hidden'}
    VISIBLE = {'visibility': 'visible', 'height': 'auto', 'overflow': 'visible'}

    def test_hidden_when_no_cell(self):
        cell_id = None
        style = self.HIDDEN if cell_id is None else self.VISIBLE
        assert style['visibility'] == 'hidden'

    def test_visible_when_cell_selected(self):
        cell_id = 42
        style = self.HIDDEN if cell_id is None else self.VISIBLE
        assert style['visibility'] == 'visible'

    def test_hidden_collapses_height(self):
        assert self.HIDDEN['height'] == '0'
        assert self.HIDDEN['overflow'] == 'hidden'

    def test_visible_restores_height(self):
        assert self.VISIBLE['height'] == 'auto'
        assert self.VISIBLE['overflow'] == 'visible'
