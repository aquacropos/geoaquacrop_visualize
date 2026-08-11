import os
import sys

# Make the project root importable so autodoc can find the module
sys.path.insert(0, os.path.abspath('..'))

# ── Project metadata ──────────────────────────────────────────────────────────
project   = 'GeoAquaCrop Visualizer'
author    = 'GIST Lab, Aalto University'
copyright = '2025, GIST Lab, Aalto University'
release   = '2.0'

# ── Extensions ────────────────────────────────────────────────────────────────
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',       # NumPy/Google docstrings
    'sphinx.ext.viewcode',       # [source] links
    'sphinx.ext.autosummary',
    'sphinx.ext.intersphinx',
]

# Napoleon settings (module uses NumPy-style docstrings)
napoleon_numpy_docstring   = True
napoleon_google_docstring  = False
napoleon_use_param         = True
napoleon_use_rtype         = True

# autodoc defaults
autodoc_default_options = {
    'members':          True,
    'undoc-members':    False,
    'show-inheritance': True,
    'member-order':     'bysource',
}

intersphinx_mapping = {
    'python':  ('https://docs.python.org/3',            None),
    'pandas':  ('https://pandas.pydata.org/docs',       None),
    'numpy':   ('https://numpy.org/doc/stable',         None),
    'xarray':  ('https://docs.xarray.dev/en/stable',    None),
    'plotly':  ('https://plotly.com/python-api-reference', None),
}

# ── HTML output ───────────────────────────────────────────────────────────────
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
