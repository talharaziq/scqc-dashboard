"""Small typed objects shared between modules.

These classes mostly carry data. Checking whether values make sense (for example
``min_genes <= max_genes``) happens where they are used, so the error can be raised
as a user-facing exception. The invariants enforced here are the ones without which an
object would be meaningless, and a violation is a programming error (ValueError).

The column names below are part of the public output format: they appear in CSV
files, in plots, and (with a prefix) in exported .h5ad files. Change them only on
purpose, and record the change.
"""

import re
from dataclasses import dataclass
from enum import StrEnum

import numpy as np

# Per-cell QC columns.
COL_TOTAL_COUNTS = "total_counts"
COL_N_GENES = "n_genes_detected"

# Per-gene QC columns.
GENE_COL_N_CELLS = "n_cells_detected"
GENE_COL_FRACTION = "fraction_of_cells"
GENE_COL_TOTAL = "total_counts"

# Prefix added to QC columns written into an exported .h5ad file, so they cannot
# collide with columns that already exist in the user's obs table.
EXPORT_COLUMN_PREFIX = "scqc_"

# Name of the mitochondrial gene set. Its percentage column is pct_counts_mito.
MITO_SET = "mito"

_SET_NAME_PATTERN = re.compile(r"[A-Za-z0-9_]+")


def pct_counts_column(set_name: str) -> str:
    """Return the name of the percentage column for a gene set, e.g. pct_counts_mito."""
    if not _SET_NAME_PATTERN.fullmatch(set_name):
        raise ValueError(
            f"Gene set name {set_name!r} may contain only letters, digits and underscores."
        )
    return f"pct_counts_{set_name}"


class InputKind(StrEnum):
    """The input formats the app can read."""

    H5AD = "h5ad"
    TENX_H5 = "10x_h5"
    TENX_MTX = "10x_mtx"


class MatrixSourceKind(StrEnum):
    """Where the expression matrix used for QC is stored in the AnnData object."""

    X = "x"
    LAYER = "layer"
    RAW = "raw"


@dataclass(frozen=True, slots=True)
class MatrixSourceSpec:
    """Identifies the matrix used for QC: ``X``, a named layer, or ``raw.X``."""

    kind: MatrixSourceKind = MatrixSourceKind.X
    layer: str | None = None

    def __post_init__(self) -> None:
        if self.kind is MatrixSourceKind.LAYER:
            if not self.layer:
                raise ValueError("A layer matrix source needs a layer name.")
        elif self.layer is not None:
            raise ValueError("Only a layer matrix source can have a layer name.")

    @property
    def label(self) -> str:
        """Human-readable name used in the UI, reports and the manifest."""
        if self.kind is MatrixSourceKind.LAYER:
            return f"layers[{self.layer!r}]"
        if self.kind is MatrixSourceKind.RAW:
            return "raw.X"
        return "X"


class Severity(StrEnum):
    """How serious a validation finding is. Only errors stop the analysis."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """One finding from input or matrix validation.

    ``code`` is a short stable identifier such as ``negative_values``. ``heuristic`` is
    True when the check is a guess (for example "values look log-transformed") and
    False when it is definitive. The UI and the report show that difference.
    ``message`` is shown to the user, so it must not contain data content.
    """

    severity: Severity
    code: str
    message: str
    heuristic: bool = False


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """All findings from validating one dataset or matrix."""

    issues: tuple[ValidationIssue, ...] = ()

    @property
    def errors(self) -> tuple[ValidationIssue, ...]:
        return tuple(i for i in self.issues if i.severity is Severity.ERROR)

    @property
    def warnings(self) -> tuple[ValidationIssue, ...]:
        return tuple(i for i in self.issues if i.severity is Severity.WARNING)

    @property
    def has_errors(self) -> bool:
        return any(i.severity is Severity.ERROR for i in self.issues)


class GeneSetStatus(StrEnum):
    """Outcome of trying to identify a gene set.

    ``NO_MATCH`` and ``NOT_CONFIGURED`` must never be reported as "0% of counts".
    """

    MATCHED = "matched"
    NO_MATCH = "no_match"
    NOT_CONFIGURED = "not_configured"


@dataclass(frozen=True, slots=True, eq=False)
class GeneSetResult:
    """The result of identifying one gene set (for example the mitochondrial genes).

    ``mask`` (one boolean per gene, in matrix order) and ``matched_names`` are present
    only when ``status`` is MATCHED. Otherwise ``reason`` explains why, and no
    percentage may be calculated. ``rule`` describes how the set was defined, for the
    UI and the manifest. Equality is by identity because the mask is an array.
    """

    name: str
    status: GeneSetStatus
    n_features_checked: int
    rule: str = ""
    reason: str | None = None
    mask: np.ndarray | None = None
    matched_names: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        pct_counts_column(self.name)  # validates the name
        if self.status is GeneSetStatus.MATCHED:
            if self.mask is None:
                raise ValueError("A matched gene set needs a mask.")
            if self.mask.dtype != np.bool_ or self.mask.shape != (self.n_features_checked,):
                raise ValueError(
                    "The gene set mask must be a boolean array with one entry per gene."
                )
            n_matched = int(self.mask.sum())
            if n_matched == 0:
                raise ValueError("A matched gene set must contain at least one gene.")
            if len(self.matched_names) != n_matched:
                raise ValueError("matched_names must have one entry per matched gene.")
        elif self.mask is not None or self.matched_names:
            raise ValueError("Only a MATCHED gene set may carry a mask or matched names.")

    @property
    def n_matched(self) -> int:
        return 0 if self.mask is None else int(self.mask.sum())

    @property
    def is_usable(self) -> bool:
        """True when a percentage can be calculated for this set."""
        return self.status is GeneSetStatus.MATCHED


@dataclass(frozen=True, slots=True)
class FilterSettings:
    """Cell-filtering thresholds. ``None`` means that rule is switched off.

    Bounds are inclusive. ``max_pct`` applies to the percentage of counts from the gene
    set named by ``pct_set``. Validation happens in qc.filters.
    """

    min_genes: int | None = None
    max_genes: int | None = None
    min_counts: float | None = None
    max_counts: float | None = None
    max_pct: float | None = None
    pct_set: str = MITO_SET

    @property
    def has_rules(self) -> bool:
        return any(
            value is not None
            for value in (
                self.min_genes,
                self.max_genes,
                self.min_counts,
                self.max_counts,
                self.max_pct,
            )
        )


@dataclass(frozen=True, slots=True)
class FilterRuleResult:
    """What one filter rule did.

    ``n_fail_alone`` is how many cells fail this rule on its own. ``n_newly_removed`` is
    how many cells this rule removed after the earlier rules had already acted, and
    ``n_remaining`` is how many cells are left after it.
    """

    rule: str
    n_fail_alone: int
    n_newly_removed: int
    n_remaining: int


@dataclass(frozen=True, slots=True)
class FilterReport:
    """Summary of applying a set of filters, in the order the rules were applied."""

    settings: FilterSettings
    n_cells_before: int
    n_cells_after: int
    rules: tuple[FilterRuleResult, ...] = ()

    @property
    def n_removed(self) -> int:
        return self.n_cells_before - self.n_cells_after


__all__ = [
    "COL_N_GENES",
    "COL_TOTAL_COUNTS",
    "EXPORT_COLUMN_PREFIX",
    "GENE_COL_FRACTION",
    "GENE_COL_N_CELLS",
    "GENE_COL_TOTAL",
    "MITO_SET",
    "FilterReport",
    "FilterRuleResult",
    "FilterSettings",
    "GeneSetResult",
    "GeneSetStatus",
    "InputKind",
    "MatrixSourceKind",
    "MatrixSourceSpec",
    "Severity",
    "ValidationIssue",
    "ValidationResult",
    "pct_counts_column",
]
