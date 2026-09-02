"""
Tests for ``geoaquacrop_plotting.config``.

Imports the real module: config has no data dependency beyond locating the
workspace, which conftest stubs out.
"""

from geoaquacrop_plotting import config


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  VARIABLE CATALOGUES                                                       ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class TestMapVariables:

    def test_map_variables_required_keys(self):
        for key, val in config.MAP_VARIABLES.items():
            assert 'label' in val, f"Missing 'label' in {key}"
            assert 'colorscale' in val, f"Missing 'colorscale' in {key}"
            assert 'sum_colorscale' in val, f"Missing 'sum_colorscale' in {key}"
            assert val['default_agg'] in ('mean', 'sum'), f"Invalid default_agg in {key}"

    def test_map_variables_not_empty(self):
        assert len(config.MAP_VARIABLES) > 0

    def test_irrigation_defaults_to_sum(self):
        assert config.MAP_VARIABLES['Seasonal irrigation (mm)']['default_agg'] == 'sum'

    def test_dry_yield_defaults_to_mean(self):
        assert config.MAP_VARIABLES['Dry yield (tonne/ha)']['default_agg'] == 'mean'


class TestDailyVariables:

    def test_daily_variables_required_keys(self):
        for key, val in config.DAILY_VARIABLES.items():
            assert 'label' in val
            assert val['table'] in ('water_flux', 'crop_growth'), f"Invalid table in {key}"
            assert val['color'].startswith('#'), f"Color must be hex in {key}"

    def test_colors_are_six_digit_hex(self):
        for key, val in config.DAILY_VARIABLES.items():
            assert len(val['color']) == 7, f"Expected #rrggbb in {key}"
            int(val['color'][1:], 16)  # raises if not hex

    def test_table_selection(self):
        assert config.DAILY_VARIABLES['Es']['table'] == 'water_flux'
        assert config.DAILY_VARIABLES['biomass']['table'] == 'crop_growth'


class TestClimateVariables:

    def test_climate_variables_required_keys(self):
        for key, val in config.CLIMATE_VARIABLES.items():
            assert 'label' in val
            assert 'map_label' in val, f"Missing 'map_label' in {key}"
            assert 'unit' in val, f"Missing 'unit' in {key}"
            assert 'colorscale' in val

    def test_precipitation_unit_is_mm_per_year(self):
        assert config.CLIMATE_VARIABLES['Precipitation']['unit'] == 'mm/year'

    def test_temperature_unit_is_celsius(self):
        assert config.CLIMATE_VARIABLES['MaxTemp']['unit'] == '°C'

    def test_temperature_map_label_same_as_label(self):
        mt = config.CLIMATE_VARIABLES['MaxTemp']
        assert mt['label'] == mt['map_label']

    def test_flux_map_label_differs_from_label(self):
        """Precipitation and ET are summed on the map, so the units differ."""

        for var in ('Precipitation', 'ReferenceET'):
            info = config.CLIMATE_VARIABLES[var]
            assert info['label'] != info['map_label'], var
            assert 'mm/day' in info['label']
            assert 'mm/year' in info['map_label']


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  SCALAR CONSTANTS                                                          ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class TestScalarConstants:

    def test_cell_res_positive(self):
        assert config.CELL_RES > 0

    def test_map_height_positive(self):
        assert config.MAP_HEIGHT > 0

    def test_ts_height_positive(self):
        assert config.TS_HEIGHT > 0

    def test_port_in_valid_range(self):
        assert 1 <= config.PORT <= 65535


class TestIrrMap:

    def test_rainfed_maps_to_rf(self):
        assert config.IRR_MAP['rainfed'] == 'rf'

    def test_irrigated_maps_to_ir(self):
        assert config.IRR_MAP['irrigated'] == 'ir'

    def test_unknown_key_fallback(self):
        irr = 'sprinkler'
        assert config.IRR_MAP.get(irr, irr) == 'sprinkler'


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  PATH RESOLUTION                                                           ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class TestPathResolution:

    def test_workspace_honours_env_override(self):
        """conftest sets GEOAQUACROP_ROOT, so the stub must win."""

        import os
        assert config._WORKSPACE == os.environ['GEOAQUACROP_ROOT']

    def test_data_paths_are_absolute(self):
        import os
        for p in (config.SUMMARY_PKL, config.DAILY_PKL,
                  config.GEOJSON_PATH, config.PROCESSED_DIR, config.EXPORT_DIR):
            assert os.path.isabs(p), p

    def test_data_paths_sit_under_workspace(self):
        for p in (config.SUMMARY_PKL, config.DAILY_PKL,
                  config.GEOJSON_PATH, config.PROCESSED_DIR):
            assert p.startswith(config._WORKSPACE), p

    def test_no_parent_traversal_left_in_paths(self):
        """The '../' style paths were replaced by workspace-anchored ones."""

        for p in (config.SUMMARY_PKL, config.DAILY_PKL,
                  config.GEOJSON_PATH, config.PROCESSED_DIR):
            assert '..' not in p, p

    def test_ascend_reaches_filesystem_root(self):
        paths = list(config._ascend('/a/b/c'))
        assert paths[0] == '/a/b/c'
        assert paths[-1] == '/'

    def test_ascend_is_monotonically_shorter(self):
        paths = list(config._ascend('/a/b/c'))
        assert paths == sorted(paths, key=len, reverse=True)
