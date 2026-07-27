"""Unit tests for application constants."""

from vacation_tracker.core.constants import (
    DEFAULT_PAGE_SIZE,
    MAX_IMPORT_FILE_SIZE_BYTES,
    MAX_PAGE_SIZE,
    SUPPORTED_IMPORT_EXTENSIONS,
    VACATION_DATE_FORMATS,
    UserRole,
)


def test_user_roles() -> None:
    assert UserRole.ADMIN == "admin"
    assert UserRole.EMPLOYEE == "employee"


def test_supported_import_extensions() -> None:
    assert SUPPORTED_IMPORT_EXTENSIONS == frozenset({".csv", ".xlsx"})


def test_vacation_date_formats_include_sample_format() -> None:
    assert "%A, %B %d, %Y" in VACATION_DATE_FORMATS


def test_limits() -> None:
    assert MAX_IMPORT_FILE_SIZE_BYTES == 5 * 1024 * 1024
    assert DEFAULT_PAGE_SIZE == 50
    assert MAX_PAGE_SIZE == 200
