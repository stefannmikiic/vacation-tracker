"""Row-level field validation for import pipelines."""

from vacation_tracker.imports.dates import parse_vacation_date
from vacation_tracker.imports.parsers.structure import (
    RawAllowanceRow,
    RawEmployeeRow,
    RawUsageRow,
)
from vacation_tracker.imports.rows import (
    AllowanceImportRow,
    AllowanceParseResult,
    EmployeeImportRow,
    EmployeeParseResult,
    ImportRowError,
    UsageImportRow,
    UsageParseResult,
)


def _is_plausible_email(email: str) -> bool:
    if not email or " " in email:
        return False
    if email.count("@") != 1:
        return False
    local, _, domain = email.partition("@")
    return bool(local) and "." in domain


def validate_employee_rows(raw_rows: list[RawEmployeeRow]) -> EmployeeParseResult:
    """Validate employee rows; keep valid rows and collect row-level errors."""
    rows: list[EmployeeImportRow] = []
    errors: list[ImportRowError] = []

    for raw in raw_rows:
        if not _is_plausible_email(raw.email):
            errors.append(
                ImportRowError(raw.row_number, f"Invalid email: {raw.email!r}")
            )
            continue
        if not raw.password:
            errors.append(ImportRowError(raw.row_number, "Password is required"))
            continue
        rows.append(
            EmployeeImportRow(
                row_number=raw.row_number,
                email=raw.email.casefold(),
                password=raw.password,
            )
        )

    return EmployeeParseResult(rows=rows, errors=errors)


def validate_allowance_rows(raw_rows: list[RawAllowanceRow]) -> AllowanceParseResult:
    """Validate allowance rows; keep valid rows and collect row-level errors."""
    rows: list[AllowanceImportRow] = []
    errors: list[ImportRowError] = []

    for raw in raw_rows:
        if not _is_plausible_email(raw.email):
            errors.append(
                ImportRowError(raw.row_number, f"Invalid email: {raw.email!r}")
            )
            continue
        try:
            total_days = int(raw.total_days)
        except ValueError:
            errors.append(
                ImportRowError(
                    raw.row_number,
                    f"Total vacation days must be an integer, got {raw.total_days!r}",
                )
            )
            continue
        if total_days < 0:
            errors.append(
                ImportRowError(
                    raw.row_number,
                    f"Total vacation days must be non-negative, got {total_days}",
                )
            )
            continue
        rows.append(
            AllowanceImportRow(
                row_number=raw.row_number,
                email=raw.email.casefold(),
                year=raw.year,
                total_days=total_days,
            )
        )

    return AllowanceParseResult(rows=rows, errors=errors)


def validate_usage_rows(raw_rows: list[RawUsageRow]) -> UsageParseResult:
    """Validate usage rows; keep valid rows and collect row-level errors."""
    rows: list[UsageImportRow] = []
    errors: list[ImportRowError] = []

    for raw in raw_rows:
        if not _is_plausible_email(raw.email):
            errors.append(
                ImportRowError(raw.row_number, f"Invalid email: {raw.email!r}")
            )
            continue

        try:
            start_date = parse_vacation_date(raw.start_date)
        except ValueError as exc:
            errors.append(ImportRowError(raw.row_number, f"Invalid start date: {exc}"))
            continue

        try:
            end_date = parse_vacation_date(raw.end_date)
        except ValueError as exc:
            errors.append(ImportRowError(raw.row_number, f"Invalid end date: {exc}"))
            continue

        if start_date > end_date:
            errors.append(
                ImportRowError(
                    raw.row_number,
                    f"Start date {start_date} is after end date {end_date}",
                )
            )
            continue

        rows.append(
            UsageImportRow(
                row_number=raw.row_number,
                email=raw.email.casefold(),
                start_date=start_date,
                end_date=end_date,
            )
        )

    return UsageParseResult(rows=rows, errors=errors)
