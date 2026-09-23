"""Interactive visualisation of gridded AquaCrop simulations.

The visualisation stage of the GeoAquaCrop toolchain. Usable on its own::

    import geoaquacrop_visualize as visualize

    visualize.run(root='/data/region')      # then open the printed URL

or through the unified toolchain façade::

    import geoaquacrop as gac

    gac.visualize.run(root='/data/region')

Loading the datasets and assembling the app happens in :func:`build_app`, which
:func:`run` calls. Importing this package does none of that, so it stays cheap
and works on a machine with no data present.
"""
import os

from importlib.metadata import PackageNotFoundError, version

__all__ = ["run", "build_app", "__version__"]

try:
    __version__ = version("geoaquacrop_visualize")
except PackageNotFoundError:          # running from source, not installed
    __version__ = "0.0.0+unknown"


def build_app(root=None, outputs=None):
    """Load the data and assemble the Dash application.

    Returns the Dash object without starting a server, for deployment behind a
    WSGI server (``app.server``) or for embedding.

    Parameters
    ----------
    root : str or Path, optional
        Workspace holding the GeoAquaCrop data trees. Sets
        ``GEOAQUACROP_ROOT`` for this process.
    outputs : str or Path, optional
        Simulation ``outputs`` folder, if it is not under ``root``. Sets
        ``GEOAQUACROP_OUTPUTS``.
    """
    if root is not None:
        os.environ["GEOAQUACROP_ROOT"] = str(root)
    if outputs is not None:
        os.environ["GEOAQUACROP_OUTPUTS"] = str(outputs)

    # imported here, not at module level: these read the datasets and build the
    # layout, which must not happen merely because someone imported the package
    from .app_shell import app
    from . import layout                                     # noqa: F401
    from . import (callbacks_controls, callbacks_selection,   # noqa: F401
                   callbacks_maps, callbacks_timeseries,
                   callbacks_export)
    return app


def run(root=None, outputs=None, port=None, debug=False, **kwargs):
    """Start the interactive dashboard, then open the printed URL.

    Every dataset is read and every aggregation computed before the server
    starts, so expect a pause proportional to the size of the run.

    Parameters
    ----------
    root, outputs : str or Path, optional
        As :func:`build_app`.
    port : int, optional
        Port to serve on. Defaults to the configured ``PORT``.
    debug : bool
        Passed to ``Dash.run``.
    **kwargs
        Further arguments passed to ``Dash.run``.
    """
    app = build_app(root, outputs)
    from .config import PORT
    app.run(debug=debug, port=port or PORT, **kwargs)