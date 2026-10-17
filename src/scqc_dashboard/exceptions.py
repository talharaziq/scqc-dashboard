"""Exception types that are safe to show to the user.

Every error this package raises on purpose derives from ScqcError. The text in
``user_message`` is written for the person using the app: it says what went wrong and
what they can try next. It must never contain matrix values, gene names, cell
barcodes, file paths, or any other content taken from the uploaded data.

``detail`` is optional extra context for server logs only. The UI shows
``user_message`` and nothing else. Unexpected exceptions (bugs) are not ScqcError:
the UI should log their traceback and show a generic message instead.

A gene set with no matching genes is not an error. It is a normal result state,
handled in qc.gene_sets.
"""


class ScqcError(Exception):
    """Base class for all expected, user-facing errors."""

    def __init__(self, user_message: str, *, detail: str | None = None) -> None:
        super().__init__(user_message)
        self.user_message = user_message
        self.detail = detail


class UnsupportedFormatError(ScqcError):
    """The file is not one of the supported input formats."""


class InputFileError(ScqcError):
    """The file looks like a supported format but is malformed, empty, or incomplete."""


class ResourceLimitError(ScqcError):
    """The file or matrix exceeds a configured size or memory limit."""


class MatrixValidationError(ScqcError):
    """The selected matrix cannot be used for count-based QC.

    Examples: negative values, NaN or infinite values, or no cells or genes.
    """


class QCCalculationError(ScqcError):
    """A QC metric could not be calculated."""


class FilterSettingsError(ScqcError):
    """The filter thresholds are invalid, for example a minimum above its maximum."""


class ExportError(ScqcError):
    """An export file could not be created or written."""


__all__ = [
    "ExportError",
    "FilterSettingsError",
    "InputFileError",
    "MatrixValidationError",
    "QCCalculationError",
    "ResourceLimitError",
    "ScqcError",
    "UnsupportedFormatError",
]
