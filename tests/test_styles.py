"""
Tests for ``geoaquacrop_plotting.styles``.

Imports the real module: styles depends only on dash and config, so these
tests exercise the shipped style factories and sidebar widgets.
"""

import pytest

from geoaquacrop_plotting import styles


class TestBtnStyle:

    PALETTE = ['blue', 'green', 'orange', 'purple', 'teal', 'red']

    @pytest.mark.parametrize('color', PALETTE)
    def test_active_and_inactive_differ(self, color):
        assert styles.btn_style(True, color) != styles.btn_style(False, color)

    @pytest.mark.parametrize('color', PALETTE)
    def test_active_is_filled_with_white_text(self, color):
        s = styles.btn_style(True, color)
        assert s['color'] == 'white'
        assert s['backgroundColor'] == s['border'].split()[-1]

    @pytest.mark.parametrize('color', PALETTE)
    def test_inactive_has_dark_text(self, color):
        assert styles.btn_style(False, color)['color'] == '#333'

    @pytest.mark.parametrize('color', PALETTE)
    def test_shared_base_properties(self, color):
        for active in (True, False):
            s = styles.btn_style(active, color)
            assert s['cursor'] == 'pointer'
            assert s['borderRadius'] == '4px'
            assert s['border'].startswith('1px solid #')

    def test_unknown_colour_raises(self):
        with pytest.raises(KeyError):
            styles.btn_style(True, 'chartreuse')


class TestDdStyle:

    def test_default_width(self):
        assert styles.dd_style()['width'] == '80px'

    def test_custom_width(self):
        assert styles.dd_style('120px')['width'] == '120px'

    def test_is_inline_block(self):
        assert styles.dd_style()['display'] == 'inline-block'


class TestStyleConstants:

    def test_font_stack_starts_with_arial(self):
        assert styles.FONT_STACK.startswith('Arial')

    def test_accent_is_hex(self):
        assert styles.ACCENT.startswith('#')
        int(styles.ACCENT[1:], 16)

    def test_sidebar_style_fills_viewport(self):
        assert styles.SIDEBAR_STYLE['minHeight'] == '100vh'

    def test_sidebar_is_positioned_for_pinned_export_button(self):
        """The export button is absolutely positioned inside the sidebar."""

        assert styles.SIDEBAR_STYLE['position'] == 'relative'

    def test_ribbon_is_flex_row(self):
        assert styles.RIBBON_STYLE['display'] == 'flex'

    def test_all_style_dicts_use_the_font_stack(self):
        for name in ('SIDEBAR_STYLE', 'RIBBON_STYLE', 'DD_CTRL_STYLE'):
            assert getattr(styles, name)['fontFamily'] == styles.FONT_STACK


class TestVariableGroups:

    def test_map_groups_partition_map_variables(self):
        from geoaquacrop_plotting.config import MAP_VARIABLES
        grouped = styles._YIELD_VARS + styles._WATER_VARS + styles._WP_VARS
        assert set(grouped) == set(MAP_VARIABLES)

    def test_map_groups_do_not_overlap(self):
        grouped = styles._YIELD_VARS + styles._WATER_VARS + styles._WP_VARS
        assert len(grouped) == len(set(grouped))

    def test_daily_groups_partition_daily_variables(self):
        from geoaquacrop_plotting.config import DAILY_VARIABLES
        grouped = styles._FLUX_VARS + styles._SOIL_VARS + styles._CROP_VARS
        assert set(grouped) == set(DAILY_VARIABLES)

    def test_daily_groups_do_not_overlap(self):
        grouped = styles._FLUX_VARS + styles._SOIL_VARS + styles._CROP_VARS
        assert len(grouped) == len(set(grouped))


class TestDropdownOptions:

    def test_map_opts_use_labels(self):
        from geoaquacrop_plotting.config import MAP_VARIABLES
        opts = styles._map_dd_opts(styles._YIELD_VARS)
        assert opts[0]['label'] == MAP_VARIABLES[styles._YIELD_VARS[0]]['label']
        assert opts[0]['value'] == styles._YIELD_VARS[0]

    def test_daily_opts_use_labels(self):
        from geoaquacrop_plotting.config import DAILY_VARIABLES
        opts = styles._daily_dd_opts(styles._FLUX_VARS)
        assert opts[0]['label'] == DAILY_VARIABLES[styles._FLUX_VARS[0]]['label']

    def test_unknown_keys_are_skipped(self):
        assert styles._map_dd_opts(['not a variable']) == []
        assert styles._daily_dd_opts(['not a variable']) == []

    def test_every_group_yields_options(self):
        for group in (styles._YIELD_VARS, styles._WATER_VARS, styles._WP_VARS):
            assert len(styles._map_dd_opts(group)) == len(group)
        for group in (styles._FLUX_VARS, styles._SOIL_VARS, styles._CROP_VARS):
            assert len(styles._daily_dd_opts(group)) == len(group)


class TestSidebarWidgets:

    def test_section_header_is_uppercase_styled(self):
        div = styles._sec_hdr('Map Variable')
        assert div.children == 'Map Variable'
        assert div.style['textTransform'] == 'uppercase'

    def test_control_label_is_block(self):
        label = styles._ctrl_label('Crop & Irrigation')
        assert label.children == 'Crop & Irrigation'
        assert label.style['display'] == 'block'
