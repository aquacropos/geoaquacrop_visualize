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

The datasets are held in module-level state in
:mod:`geoaquacrop_visualize.data`, read once when that module is first
imported. One process therefore serves one workspace: calling :func:`build_app`
a second time with a different ``root`` returns the app built from the first.
Use a separate process per workspace.
"""
import os

from importlib.metadata import PackageNotFoundError, version

__all__ = ["run", "build_app", "main", "__version__"]

try:
    __version__ = version("geoaquacrop_visualize")
except PackageNotFoundError:          # running from source, not installed
    __version__ = "0.0.0+unknown"


#: Keyword arguments of :func:`build_app` mapped to the environment variables
#: :mod:`geoaquacrop_visualize.config` reads. Keeping the mapping in one place
#: means a new location needs adding in exactly one spot.
_ENVIRONMENT = {
    "root":      "GEOAQUACROP_ROOT",
    "outputs":   "GEOAQUACROP_OUTPUTS",
    "processed": "GEOAQUACROP_PROCESSED",
    "region":    "GEOAQUACROP_REGION",
    "exports":   "GEOAQUACROP_EXPORTS",
}


def _apply_locations(**locations):
    """Publish the given locations to the environment, ignoring any left unset."""
    for keyword, value in locations.items():
        if value is not None:
            os.environ[_ENVIRONMENT[keyword]] = str(value)


def _check_inputs(config):
    """Raise if any required input is missing, naming every one of them.

    Checked before the datasets are read, so a missing workspace produces one
    sentence naming the paths that were tried rather than a traceback from
    whichever loader happened to run first.
    """
    required = [
        ("region boundary",     config.GEOJSON_PATH),
        ("summary results",     config.SUMMARY_PKL),
        ("daily results",       config.DAILY_PKL),
        ("preprocessed inputs", config.PROCESSED_DIR),
    ]
    missing = [(what, path) for what, path in required
               if not os.path.exists(path)]
    if not missing:
        return

    listed = "\n".join(f"  {what:<20} {path}" for what, path in missing)
    raise FileNotFoundError(
        f"Cannot start: {len(missing)} required input(s) not found under "
        f"workspace root '{config.ROOT}'.\n{listed}\n\n"
        "Point the app at a workspace produced by geoaquacrop_preprocess and "
        "geoaquacrop_simulate, with run(root=...) or the --root option. "
        "Individual locations can be set with --outputs, --processed, "
        "--region and --exports."
    )


def build_app(root=None, outputs=None, processed=None, region=None,
              exports=None):
    """Load the data and assemble the Dash application.

    Returns the Dash object without starting a server, for deployment behind a
    WSGI server (``app.server``) or for embedding.

    Parameters
    ----------
    root : str or Path, optional
        Workspace holding the GeoAquaCrop data trees. The other locations
        default to subdirectories of it. Defaults to the working directory.
    outputs, processed, region, exports : str or Path, optional
        Individual locations, for a workspace whose parts are not all under
        ``root``.

    Raises
    ------
    FileNotFoundError
        If any required input is missing. Every missing path is named.
    """
    _apply_locations(root=root, outputs=outputs, processed=processed,
                     region=region, exports=exports)

    # imported here, not at module level: config reads the environment as it is
    # imported, so the assignments above must happen first
    from . import config

    _check_inputs(config)
    os.makedirs(config.EXPORT_DIR, exist_ok=True)

    # these read the datasets and build the layout, which must not happen
    # merely because someone imported the package
    from .app_shell import app
    from . import layout                                     # noqa: F401
    from . import (callbacks_controls, callbacks_selection,   # noqa: F401
                   callbacks_maps, callbacks_timeseries,
                   callbacks_export)
    return app


def run(root=None, outputs=None, processed=None, region=None, exports=None,
        port=None, debug=False, **kwargs):
    """Start the interactive dashboard, then open the printed URL.

    Every dataset is read and every aggregation computed before the server
    starts, so expect a pause proportional to the size of the run.

    Parameters
    ----------
    root, outputs, processed, region, exports : str or Path, optional
        As :func:`build_app`.
    port : int, optional
        Port to serve on. Defaults to the configured ``PORT``.
    debug : bool
        Passed to ``Dash.run``.
    **kwargs
        Further arguments passed to ``Dash.run``.
    """
    app = build_app(root=root, outputs=outputs, processed=processed,
                    region=region, exports=exports)
    from .config import PORT
    app.run(debug=debug, port=port or PORT, **kwargs)


def main(argv=None):
    """Command-line entry point for the ``geoaquacrop_visualize`` script."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="geoaquacrop_visualize",
        description="Launch the GeoAquaCrop results dashboard.",
    )
    parser.add_argument("--root", help="Workspace root. Defaults to the "
                                       "working directory.")
    parser.add_argument("--outputs", help="Simulation outputs directory.")
    parser.add_argument("--processed", help="Preprocessed NetCDF directory.")
    parser.add_argument("--region", help="Region boundary GeoJSON.")
    parser.add_argument("--exports", help="Directory for exported files.")
    parser.add_argument("--port", type=int, help="Port to serve on.")
    parser.add_argument("--debug", action="store_true",
                        help="Run Dash in debug mode.")
    parser.add_argument("--version", action="version",
                        version=f"geoaquacrop_visualize {__version__}")
    args = parser.parse_args(argv)

    try:
        run(root=args.root, outputs=args.outputs, processed=args.processed,
            region=args.region, exports=args.exports,
            port=args.port, debug=args.debug)
    except FileNotFoundError as error:
        parser.exit(2, f"{parser.prog}: error: {error}\n")
