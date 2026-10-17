"""SCQC Dashboard: a local quality-control explorer for single-cell RNA-seq data."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("scqc-dashboard")
except PackageNotFoundError:
    # Running from a source checkout that was never installed in this environment.
    __version__ = "unknown"

__all__ = ["__version__"]


