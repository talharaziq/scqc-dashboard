# Decision log

This file records the decisions that shape the project: what was decided, why, and what
it costs. New entries go at the bottom. Every entry is accepted unless it says otherwise.

Last updated: 2026-10-17

## Compatibility facts

Checked on the PyPI project pages on 2026-10-17:

- scanpy 1.12.4 (released 2026-08-27) requires Python 3.12 or newer and lists 3.12 to 3.14.
- anndata 0.13.4 (released 2026-09-18) requires Python 3.12 or newer and lists 3.12 to 3.14.
- streamlit 1.61.1 requires Python 3.10 or newer and lists 3.10 to 3.14. Version 1.66.0
  was released on 2026-10-14.
- scanpy 1.13.0a2 is a pre-release and is not used.

Installed on 2026-10-17 in GitHub Codespaces (Linux, Python 3.14.2) with
`pip install -e ".[dev]"`:

- anndata 0.13.4, scanpy 1.12.4, streamlit 1.66.0
- numpy 2.5.4, scipy 1.18.1, pandas 3.0.6, h5py 3.16.0, plotly 7.1.0

With these versions, `pip check` reported no broken requirements, the package imported,
and `ruff check` and `ruff format --check` passed. So scanpy 1.12.4 and anndata 0.13.4
resolve together. No tests exist yet, so nothing beyond install and import is verified.
The exact versions of pytest and ruff were not recorded.

Not verified yet:

- Python 3.12 and 3.13 (local runs use 3.14), Windows and macOS.
- How anndata 0.13.4 handles pandas 3, a new major version, when writing and reading h5ad
  files, especially string columns in obs and var. The h5ad round-trip tests must cover it.
- Whether `st.navigation` and Streamlit's `AppTest` work at the declared minimum
  (`streamlit>=1.50`).

## Environment findings

Android with Termux, Python 3.13: `pip install -e ".[dev]"` failed on the first package.
No prebuilt numpy wheel was available for the platform, so pip fell back to building from
source. That needed ninja and then cmake, and the cmake compile was killed partway, most
likely because the device ran out of memory. The same problem is likely for scipy, pandas,
h5py, pyarrow (needed by Streamlit) and, through Scanpy, numba and llvmlite. Termux is not
a supported environment for this project. See D13.

## D1. Python 3.12 or newer, lower-bound dependencies only

Scanpy and anndata both require Python 3.12 or newer, so the project does too. CI runs on
3.12, 3.13 and 3.14. Day-to-day development runs on 3.14, so code is written for 3.12
(ruff's `target-version` enforces the syntax) and CI is what checks library behaviour on
3.12.

Dependencies in `pyproject.toml` have lower bounds only. After the first green test run,
the exact installed versions are frozen into a constraints file, and the date is added to
this file. Cost: Python 3.11 and older cannot install the project. Without upper bounds, a
new upstream release can break the project, and the constraints file is how we notice.

## D2. Own QC metric code, Scanpy as a cross-check

The per-cell and per-gene metrics are written with numpy and scipy sparse operations and
tested against hand-computed values. One test compares the results with Scanpy's
`calculate_qc_metrics`. Scanpy is still used to read 10x files. The guide allowed Scanpy
for QC "where appropriate"; this keeps every definition visible in our own code, and keeps
Scanpy's defaults (such as extra log columns) out of the outputs.

Scanpy stays a core dependency (owner decision, 2026-10-17). The alternative was an
optional extra, which would keep numba and llvmlite out of the core install. It was
considered and declined. Revisit it if Scanpy fails to install on another platform.

## D3. Keep the source object plus a mask

One AnnData object is loaded per upload and treated as read-only. Filtering produces a
boolean mask over the QC table. The filtered AnnData copy is built only at export. This
settles the guide's tension between keeping an untouched source and avoiding repeated
copies of large matrices. Cost: the export step needs enough memory for one filtered copy.

## D4. Dependencies live in `pyproject.toml` only

`requirements.txt`, `requirements-dev.txt` and `environment.yml` are dropped. The guide
itself warned about duplicated dependency lists. Install with `pip install -e ".[dev]"`.

## D5. One workflow module

`services/workflow.py` replaces the guide's `analysis_service.py` and
`workflow_service.py`. The two had overlapping roles, and one module is enough until it
grows.

## D6. No plots in the HTML report in version 1

Static plot images need an extra rendering dependency (kaleido), and interactive plots
need a script loaded from a CDN, which conflicts with the rule that the app makes no
external requests. The v1 report contains text and tables. Plots stay in the app.

## D7. `raw.X` is a selectable matrix source

Many h5ad files keep raw counts in `raw.X` while `X` holds normalised values. The user
chooses between `X`, a named layer, or `raw.X`. Gene annotations come from the matching
`var` table (`raw.var` for `raw.X`).

## D8. Staged releases

- 0.1: h5ad input only, QC, filtering, and exports (filtered h5ad, CSV, JSON manifest).
- 0.2: adds 10x HDF5 and Matrix Market input and the HTML report.
- 1.0: the full version 1 scope from the guide, after the validation pass.

## D9. NaN, never zero, when a percentage cannot be calculated

A cell with zero total counts gets NaN for every percentage. A gene set that matched no
genes, or was never configured, produces NaN with a visible reason. The three gene-set
states (matched, no match, not configured) are separate values in `models.py`, and only
"matched" allows a percentage.

## D10. Which matrix problems stop QC and which only warn

Negative values, NaN or infinite values, or a matrix with no cells or no genes stop QC.
Non-integer values, or a value range that looks log-transformed, produce warnings worded
as heuristics. The app never decides that a matrix "is" raw counts.

## D11. Filter semantics

Bounds are inclusive. Enabled rules are combined with AND and applied in a fixed order.
The report shows, for each rule, how many cells fail it alone and how many it removed
after earlier rules. A NaN value fails an enabled rule that depends on it. An empty
result is allowed, but export is disabled. Settings are validated (minimum not above
maximum, percentages between 0 and 100).

## D12. Smaller file set than the guide

The guide listed 76 files. Version 1 plans for 40, plus empty `__init__.py` files.
Dropped for now: `.editorconfig`, `.gitattributes`, pre-commit config, `scripts/`,
the `data/` and `examples/` READMEs, `ui/components.py`, and most of the extra docs.
`SECURITY.md`, `CITATION.cff` (needs the owner's author details) and `CHANGELOG.md` are
added before any public announcement. Other files return when there is a real need.

## D13. Development environment and platform support

Development and testing run in GitHub Codespaces (Linux, Python 3.14.2), chosen on
2026-10-17 after the Termux install failed. Linux is the only verified platform. Windows
and macOS are untested. Android with Termux is not supported, because the scientific
dependencies have no prebuilt wheels there. Files are edited in Codespaces. Any copy
elsewhere is treated as stale until it is pulled.

## Open items

- License: the owner chooses before `LICENSE` is created.
- Author name and repository URL for `CITATION.cff`.
- Freeze the constraints file after the first green test run (Phase B), then record the date.
- Confirm the HDF5 metadata layout used by the size checks in `io/limits.py` (tests).
- Confirm the `calculate_qc_metrics` call signature in the Scanpy cross-check test.
- Confirm h5ad round-trips with pandas 3 string columns (Phase B and D tests).
- Confirm `AppTest` behaviour at the declared Streamlit minimum (Phase E).
