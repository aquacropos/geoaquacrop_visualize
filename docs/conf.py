"""Sphinx configuration for geoaquacrop-visualize documentation."""
import importlib.metadata
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath("../src"))

# ---------------------------------------------------------------------------
# Project information
# ---------------------------------------------------------------------------
project   = "geoaquacrop-visualize"
author    = "Seyed Hossein Hosseini"
copyright = f"{datetime.now():%Y}, {author}"

try:
    release = importlib.metadata.version("geoaquacrop_visualize")
except importlib.metadata.PackageNotFoundError:
    release = "0.1.0"
version = ".".join(release.split(".")[:2])

# ---------------------------------------------------------------------------
# General configuration
# ---------------------------------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx.ext.autosummary",
]

templates_path   = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# ---------------------------------------------------------------------------
# Autodoc
# ---------------------------------------------------------------------------
autodoc_mock_imports = [
    "dash",
    "dash_bootstrap_components",
    "plotly",
    "pandas",
    "numpy",
    "xarray",
    "netCDF4",
    "rasterio",
    "scipy",
]

autodoc_default_options = {
    "members":          True,
    "undoc-members":    False,
    "show-inheritance": True,
    "member-order":     "bysource",
}
autodoc_typehints    = "description"
autosummary_generate = True

# ---------------------------------------------------------------------------
# Napoleon
# ---------------------------------------------------------------------------
napoleon_google_docstring         = True
napoleon_numpy_docstring          = True
napoleon_include_init_with_doc    = False
napoleon_include_private_with_doc = False
napoleon_use_rtype                = True
napoleon_use_param                = True

# ---------------------------------------------------------------------------
# Intersphinx
# ---------------------------------------------------------------------------
intersphinx_mapping = {
    "python":   ("https://docs.python.org/3",                None),
    "numpy":    ("https://numpy.org/doc/stable",              None),
    "pandas":   ("https://pandas.pydata.org/docs",            None),
    "xarray":   ("https://docs.xarray.dev/en/stable",         None),
    "plotly":   ("https://plotly.com/python-api-reference/",  None),
    "preproc":  ("https://geoaquacrop_preprocessing.readthedocs.io/en/stable/", None),
    "simulate": ("https://geoaquacrop_simulate.readthedocs.io/en/stable/",      None),
}

# ---------------------------------------------------------------------------
# HTML output
# ---------------------------------------------------------------------------
html_theme       = "furo"
html_static_path = ["_static"]
html_title       = f"{project} {version}"
