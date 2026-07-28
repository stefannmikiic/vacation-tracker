"""Dispatch tabular file reading by extension."""

from pathlib import Path

from vacation_tracker.core.constants import SUPPORTED_IMPORT_EXTENSIONS
from vacation_tracker.core.exceptions import ImportStructureError
from vacation_tracker.imports.parsers.csv_parser import read_csv_rows
from vacation_tracker.imports.parsers.excel_parser import read_excel_rows


def read_tabular_rows(content: bytes, filename: str) -> list[list[str]]:
    """Read CSV or Excel bytes into a grid of stripped strings."""
    extension = Path(filename).suffix.lower()
    if extension not in SUPPORTED_IMPORT_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_IMPORT_EXTENSIONS))
        raise ImportStructureError(
            f"Unsupported file extension {extension!r}; expected one of: {supported}"
        )

    if not content:
        raise ImportStructureError("Import file is empty")

    if extension == ".csv":
        rows = read_csv_rows(content)
    else:
        rows = read_excel_rows(content)

    if not rows:
        raise ImportStructureError("Import file has no rows")

    return rows
