"""Import pipeline: parse file → validate rows (no database writes)."""

from vacation_tracker.imports.parsers.structure import (
    extract_allowance_rows,
    extract_employee_rows,
    extract_usage_rows,
)
from vacation_tracker.imports.parsers.tabular import read_tabular_rows
from vacation_tracker.imports.rows import (
    AllowanceParseResult,
    EmployeeParseResult,
    UsageParseResult,
)
from vacation_tracker.imports.validators import (
    validate_allowance_rows,
    validate_employee_rows,
    validate_usage_rows,
)


def parse_employees(content: bytes, filename: str) -> EmployeeParseResult:
    """Parse and validate an employee profiles import file."""
    table = read_tabular_rows(content, filename)
    raw_rows = extract_employee_rows(table)
    return validate_employee_rows(raw_rows)


def parse_allowances(content: bytes, filename: str) -> AllowanceParseResult:
    """Parse and validate a vacation allowances import file."""
    table = read_tabular_rows(content, filename)
    raw_rows = extract_allowance_rows(table)
    return validate_allowance_rows(raw_rows)


def parse_usages(content: bytes, filename: str) -> UsageParseResult:
    """Parse and validate a used-vacation dates import file."""
    table = read_tabular_rows(content, filename)
    raw_rows = extract_usage_rows(table)
    return validate_usage_rows(raw_rows)
