"""Extract structured raw rows from tabular grids.

Responsible for metadata/header detection only — not field validation.
"""

from dataclasses import dataclass

from vacation_tracker.core.exceptions import ImportStructureError

_METADATA_LABEL = "vacation year"

_EMPLOYEE_HEADERS = ("employee email", "employee password")
_ALLOWANCE_HEADERS = ("employee", "total vacation days")
_USAGE_HEADERS = ("employee", "vacation start date", "vacation end date")


@dataclass(frozen=True)
class RawEmployeeRow:
    row_number: int
    email: str
    password: str


@dataclass(frozen=True)
class RawAllowanceRow:
    row_number: int
    email: str
    year: int
    total_days: str


@dataclass(frozen=True)
class RawUsageRow:
    row_number: int
    email: str
    start_date: str
    end_date: str


def _normalize_cell(value: str) -> str:
    return value.strip().casefold()


def _is_metadata_row(row: list[str]) -> bool:
    return bool(row) and _normalize_cell(row[0]) == _METADATA_LABEL


def _parse_metadata_year(row: list[str], row_number: int) -> int:
    if len(row) < 2 or not row[1].strip():
        raise ImportStructureError(
            f"Row {row_number}: metadata row is missing a vacation year value"
        )
    try:
        return int(row[1].strip())
    except ValueError as exc:
        raise ImportStructureError(
            f"Row {row_number}: vacation year must be an integer, got {row[1]!r}"
        ) from exc


def _header_matches(row: list[str], expected: tuple[str, ...]) -> bool:
    if len(row) < len(expected):
        return False
    actual = tuple(_normalize_cell(cell) for cell in row[: len(expected)])
    return actual == expected


def _require_header(
    rows: list[list[str]],
    *,
    start_index: int,
    expected: tuple[str, ...],
    label: str,
) -> int:
    """Return the index of the header row or raise ImportStructureError."""
    if start_index >= len(rows):
        raise ImportStructureError(f"Missing required header row for {label}")

    header_index = start_index
    if not _header_matches(rows[header_index], expected):
        raise ImportStructureError(
            f"Missing or invalid header row for {label}; "
            f"expected columns: {', '.join(expected)}"
        )
    return header_index


def extract_employee_rows(table: list[list[str]]) -> list[RawEmployeeRow]:
    """Parse employee profile table into raw rows. Skips optional metadata."""
    index = 0
    if _is_metadata_row(table[0]):
        index = 1

    header_index = _require_header(
        table,
        start_index=index,
        expected=_EMPLOYEE_HEADERS,
        label="employee profiles",
    )

    raw_rows: list[RawEmployeeRow] = []
    for offset, row in enumerate(table[header_index + 1 :], start=header_index + 2):
        if not any(cell.strip() for cell in row):
            continue
        email = row[0].strip() if len(row) > 0 else ""
        password = row[1].strip() if len(row) > 1 else ""
        raw_rows.append(
            RawEmployeeRow(row_number=offset, email=email, password=password)
        )

    return raw_rows


def extract_allowance_rows(table: list[list[str]]) -> list[RawAllowanceRow]:
    """Parse allowance table; metadata year is required."""
    if not _is_metadata_row(table[0]):
        raise ImportStructureError(
            "Allowance import requires a metadata row like: Vacation year,<year>"
        )

    year = _parse_metadata_year(table[0], row_number=1)
    header_index = _require_header(
        table,
        start_index=1,
        expected=_ALLOWANCE_HEADERS,
        label="vacation allowances",
    )

    raw_rows: list[RawAllowanceRow] = []
    for offset, row in enumerate(table[header_index + 1 :], start=header_index + 2):
        if not any(cell.strip() for cell in row):
            continue
        email = row[0].strip() if len(row) > 0 else ""
        total_days = row[1].strip() if len(row) > 1 else ""
        raw_rows.append(
            RawAllowanceRow(
                row_number=offset,
                email=email,
                year=year,
                total_days=total_days,
            )
        )

    return raw_rows


def extract_usage_rows(table: list[list[str]]) -> list[RawUsageRow]:
    """Parse used-vacation table; no metadata row expected."""
    header_index = _require_header(
        table,
        start_index=0,
        expected=_USAGE_HEADERS,
        label="vacation usages",
    )

    raw_rows: list[RawUsageRow] = []
    for offset, row in enumerate(table[header_index + 1 :], start=header_index + 2):
        if not any(cell.strip() for cell in row):
            continue
        email = row[0].strip() if len(row) > 0 else ""
        start_date = row[1].strip() if len(row) > 1 else ""
        end_date = row[2].strip() if len(row) > 2 else ""
        raw_rows.append(
            RawUsageRow(
                row_number=offset,
                email=email,
                start_date=start_date,
                end_date=end_date,
            )
        )

    return raw_rows
