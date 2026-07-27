"""Shared constants — avoid magic strings in application code."""

from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "admin"
    EMPLOYEE = "employee"


SUPPORTED_IMPORT_EXTENSIONS: frozenset[str] = frozenset({".csv", ".xlsx"})

# Sample used-vacation dates look like: "Friday, August 30, 2019"
VACATION_DATE_FORMATS: tuple[str, ...] = (
    "%A, %B %d, %Y",
    "%Y-%m-%d",
)

MAX_IMPORT_FILE_SIZE_BYTES: int = 5 * 1024 * 1024  # 5 MiB
DEFAULT_PAGE_SIZE: int = 50
MAX_PAGE_SIZE: int = 200
