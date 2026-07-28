"""Dataclasses for import pipeline rows and results."""

from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True)
class ImportRowError:
    """A single row-level validation failure."""

    row_number: int
    message: str


@dataclass(frozen=True)
class EmployeeImportRow:
    """Validated employee profile row ready for persistence."""

    row_number: int
    email: str
    password: str


@dataclass(frozen=True)
class AllowanceImportRow:
    """Validated yearly allowance row ready for persistence."""

    row_number: int
    email: str
    year: int
    total_days: int


@dataclass(frozen=True)
class UsageImportRow:
    """Validated used-vacation range ready for persistence."""

    row_number: int
    email: str
    start_date: date
    end_date: date


@dataclass(frozen=True)
class EmployeeParseResult:
    rows: list[EmployeeImportRow] = field(default_factory=list)
    errors: list[ImportRowError] = field(default_factory=list)


@dataclass(frozen=True)
class AllowanceParseResult:
    rows: list[AllowanceImportRow] = field(default_factory=list)
    errors: list[ImportRowError] = field(default_factory=list)


@dataclass(frozen=True)
class UsageParseResult:
    rows: list[UsageImportRow] = field(default_factory=list)
    errors: list[ImportRowError] = field(default_factory=list)
