"""
Locates the ``geoaquacrop_plotting`` package for the test suite.

The same test files are used by two project layouts:

    flat layout                    src layout
    ───────────                    ──────────
    project/                       project/
    ├── geoaquacrop_plotting/      ├── src/
    └── tests/                     │   └── geoaquacrop_plotting/
                                   └── tests/

Rather than hard-coding either shape, the package is found by checking both
candidates next to the test directory. ``conftest`` uses ``IMPORT_ROOT`` for
``sys.path`` and ``PKG_DIR`` for the stub package's ``__path__``;
``test_package_structure`` reads the sources straight from ``PKG_DIR``.
"""

import pathlib

TESTS_DIR = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = TESTS_DIR.parent

#: Candidate package locations, in priority order.
CANDIDATES = (
    PROJECT_ROOT / 'geoaquacrop_plotting',
    PROJECT_ROOT / 'src' / 'geoaquacrop_plotting',
)


def find_package_dir():
    """Return the directory of the geoaquacrop_plotting package."""

    for candidate in CANDIDATES:
        if (candidate / '__init__.py').is_file():
            return candidate
    searched = '\n  '.join(str(c) for c in CANDIDATES)
    raise RuntimeError(
        f'Could not find the geoaquacrop_plotting package.\n  Searched:\n  {searched}'
    )


#: Directory holding the package's modules.
PKG_DIR = find_package_dir()

#: Directory that must be on sys.path for ``import geoaquacrop_plotting`` to work.
IMPORT_ROOT = PKG_DIR.parent
