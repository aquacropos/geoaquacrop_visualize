"""
Structural tests for the ``geoaquacrop_plotting`` package itself.

These do not need the dataset: they read the source with ``ast`` rather than
importing the data-loading modules. They guard the properties the split was
built to guarantee — bounded module size, an acyclic dependency graph, and
data loading that happens exactly once.
"""

import ast

import pytest

from _paths import PKG_DIR as PKG

MODULES = sorted(p.name for p in PKG.glob('*.py'))

MAX_LINES = 500

#: Modules that must stay importable without the simulation data present.
DATA_FREE = {'config.py', 'utils.py', 'styles.py', 'app_shell.py'}


def imports_of(path):
    """Return the set of sibling module names a file imports from."""

    tree = ast.parse(path.read_text(encoding='utf-8'))
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.level == 1:
            if node.module:
                out.add(node.module)
            else:
                out.update(a.name for a in node.names)
    return out


class TestModuleInventory:

    def test_package_exists(self):
        assert PKG.is_dir()

    def test_has_an_init(self):
        assert '__init__.py' in MODULES

    def test_expected_modules_present(self):
        expected = {
            '__init__.py', 'config.py', 'utils.py', 'data.py', 'grid.py',
            'boundary.py',
            'aggregates.py', 'queries.py', 'export.py', 'figures_maps.py',
            'figures_timeseries.py', 'styles.py', 'app_shell.py',
            'layout_sidebar.py', 'layout_panels.py', 'layout_export.py',
            'layout.py', 'callbacks_controls.py', 'callbacks_selection.py',
            'callbacks_maps.py', 'callbacks_timeseries.py', 'callbacks_export.py',
        }
        assert set(MODULES) == expected


class TestModuleSize:

    @pytest.mark.parametrize('name', MODULES)
    def test_module_under_line_limit(self, name):
        n = len((PKG / name).read_text(encoding='utf-8').splitlines())
        assert n <= MAX_LINES, f'{name} has {n} lines (limit {MAX_LINES})'

    @pytest.mark.parametrize('name', MODULES)
    def test_module_parses(self, name):
        ast.parse((PKG / name).read_text(encoding='utf-8'))

    @pytest.mark.parametrize('name', MODULES)
    def test_module_has_a_docstring(self, name):
        tree = ast.parse((PKG / name).read_text(encoding='utf-8'))
        assert ast.get_docstring(tree), f'{name} has no module docstring'


class TestDependencyGraph:

    def test_no_import_cycles(self):
        graph = {name[:-3]: {m for m in imports_of(PKG / name)}
                 for name in MODULES if name != '__init__.py'}
        colour = {}

        def visit(node, stack):
            if colour.get(node) == 'done':
                return
            if colour.get(node) == 'open':
                pytest.fail(f'Import cycle: {" -> ".join(stack + [node])}')
            colour[node] = 'open'
            for dep in sorted(graph.get(node, ())):
                if dep in graph:
                    visit(dep, stack + [node])
            colour[node] = 'done'

        for node in sorted(graph):
            visit(node, [])

    def test_config_depends_on_nothing(self):
        assert imports_of(PKG / 'config.py') == set()

    def test_utils_depends_only_on_config(self):
        assert imports_of(PKG / 'utils.py') <= {'config'}

    def test_app_shell_depends_on_nothing(self):
        """app_shell must stay import-free so every callback module can use it."""

        assert imports_of(PKG / 'app_shell.py') == set()

    def test_data_depends_only_on_config(self):
        assert imports_of(PKG / 'data.py') <= {'config'}

    def test_figures_do_not_import_callbacks(self):
        for name in ('figures_maps.py', 'figures_timeseries.py'):
            assert not any(d.startswith('callbacks') for d in imports_of(PKG / name))

    def test_layout_does_not_import_callbacks(self):
        for name in ('layout.py', 'layout_sidebar.py',
                     'layout_panels.py', 'layout_export.py'):
            assert not any(d.startswith('callbacks') for d in imports_of(PKG / name))

    def test_callbacks_do_not_import_each_other(self):
        for name in MODULES:
            if not name.startswith('callbacks'):
                continue
            deps = {d for d in imports_of(PKG / name) if d.startswith('callbacks')}
            assert deps == set(), f'{name} imports {deps}'


class TestDataLoadedOnce:

    def test_only_data_module_opens_the_pickles(self):
        """Any second reader would double the startup cost and memory."""

        offenders = []
        for name in MODULES:
            if name == 'data.py':
                continue
            src = (PKG / name).read_text(encoding='utf-8')
            if 'pickle.load' in src or 'open_dataset' in src:
                offenders.append(name)
        assert offenders == []

    def test_data_free_modules_avoid_the_data_module(self):
        for name in DATA_FREE:
            assert 'data' not in imports_of(PKG / name), name


class TestDataFreeImports:
    """The modules the test suite imports directly must stay data-free."""

    def test_config_importable(self):
        from geoaquacrop_plotting import config
        assert config.CELL_RES > 0

    def test_utils_importable(self):
        from geoaquacrop_plotting import utils
        assert callable(utils.hex_to_rgba)

    def test_styles_importable(self):
        from geoaquacrop_plotting import styles
        assert callable(styles.btn_style)

    def test_app_shell_importable(self):
        from geoaquacrop_plotting import app_shell
        assert app_shell.app is not None

    def test_app_has_the_expected_title(self):
        from geoaquacrop_plotting import app_shell
        assert '<title>GeoAquaCrop Visualizer</title>' in app_shell.app.index_string
