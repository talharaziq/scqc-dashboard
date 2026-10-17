"""Central defaults and limits.

The numbers below are starting values for a typical laptop. They are not scientific
thresholds and have not been tuned against any dataset. Change them if your machine or
data call for it, either by editing this file or with the environment variables read in
``load_limits``. Streamlit has its own upload cap (``server.maxUploadSize`` in
``.streamlit/config.toml``); keep it at least as large as ``max_upload_bytes``.
"""

import os
from collections.abc import Mapping
from dataclasses import dataclass

TOOL_NAME = "scqc-dashboard"
APP_TITLE = "SCQC Dashboard"

# File extensions offered in the upload widget, without the leading dot. This is only a
# hint to the browser. What a file really is gets decided from its contents.
UPLOAD_SUFFIXES: tuple[str, ...] = ("h5ad",)

# Seed for the random sample used to thin out plots, so a given dataset always gives
# the same figure.
PLOT_SAMPLE_SEED = 0

_MIB = 1024 * 1024


@dataclass(frozen=True, slots=True)
class Limits:
    """Resource limits checked before an expensive operation starts."""

    # Largest accepted upload. A small compressed file can still expand a lot in memory,
    # so the checks on matrix size and estimated memory matter more than this one.
    max_upload_bytes: int = 500 * _MIB
    max_cells: int = 500_000
    max_genes: int = 100_000
    # Upper bound for the estimated in-memory size of the expression matrix.
    max_estimated_memory_bytes: int = 4096 * _MIB
    # Most points drawn in a scatter plot. Larger datasets are sampled and the UI says so.
    plot_max_points: int = 50_000
    # How many stored values are inspected by the "does this look like counts" heuristics.
    heuristic_sample_size: int = 100_000


def _positive_int(source: Mapping[str, str], name: str, default: int) -> int:
    raw = source.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        value = int(raw)
    except ValueError:
        raise ValueError(f"Environment variable {name} must be a whole number, got {raw!r}.") from None
    if value <= 0:
        raise ValueError(f"Environment variable {name} must be greater than zero, got {value}.")
    return value


def load_limits(env: Mapping[str, str] | None = None) -> Limits:
    """Build the limits from the defaults, applying any environment overrides.

    Recognised variables: SCQC_MAX_UPLOAD_MB, SCQC_MAX_CELLS, SCQC_MAX_GENES,
    SCQC_MAX_MEMORY_MB, SCQC_PLOT_MAX_POINTS. A bad value raises ValueError, which is
    a deployment mistake and not something to show to an end user.
    """
    source = os.environ if env is None else env
    defaults = Limits()
    return Limits(
        max_upload_bytes=_positive_int(
            source, "SCQC_MAX_UPLOAD_MB", defaults.max_upload_bytes // _MIB
        )
        * _MIB,
        max_cells=_positive_int(source, "SCQC_MAX_CELLS", defaults.max_cells),
        max_genes=_positive_int(source, "SCQC_MAX_GENES", defaults.max_genes),
        max_estimated_memory_bytes=_positive_int(
            source, "SCQC_MAX_MEMORY_MB", defaults.max_estimated_memory_bytes // _MIB
        )
        * _MIB,
        plot_max_points=_positive_int(
            source, "SCQC_PLOT_MAX_POINTS", defaults.plot_max_points
        ),
        heuristic_sample_size=defaults.heuristic_sample_size,
    )


__all__ = [
    "APP_TITLE",
    "PLOT_SAMPLE_SEED",
    "TOOL_NAME",
    "UPLOAD_SUFFIXES",
    "Limits",
    "load_limits",
]
