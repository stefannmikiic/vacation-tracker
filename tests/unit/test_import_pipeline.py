"""Unit tests for import pipeline parsing (CSV, no DB)."""

from datetime import date

import pytest

from vacation_tracker.core.exceptions import ImportStructureError
from vacation_tracker.imports.pipeline import (
    parse_allowances,
    parse_employees,
    parse_usages,
)


def test_parse_employees_happy_path() -> None:
    csv = (
        b"Vacation year,2019\n"
        b"Employee Email,Employee Password\n"
        b"user1@example.com,Secret1!\n"
        b"user2@example.com,Secret2!\n"
    )

    result = parse_employees(csv, "employees.csv")

    assert len(result.rows) == 2
    assert result.errors == []
    assert result.rows[0].email == "user1@example.com"
    assert result.rows[0].password == "Secret1!"
    assert result.rows[0].row_number == 3


def test_parse_employees_row_error_keeps_valid_rows() -> None:
    csv = (
        b"Employee Email,Employee Password\n"
        b"not-an-email,Secret1!\n"
        b"ok@example.com,Secret2!\n"
    )

    result = parse_employees(csv, "employees.csv")

    assert len(result.rows) == 1
    assert result.rows[0].email == "ok@example.com"
    assert len(result.errors) == 1
    assert result.errors[0].row_number == 2


def test_parse_employees_missing_header_fails_whole_file() -> None:
    csv = b"email,password\nuser@example.com,Secret1!\n"

    with pytest.raises(ImportStructureError, match="header"):
        parse_employees(csv, "employees.csv")


def test_parse_allowances_reads_year_from_metadata() -> None:
    csv = (
        b"Vacation year,2020\n"
        b"Employee,Total vacation days\n"
        b"user1@example.com,20\n"
        b"user2@example.com,15\n"
    )

    result = parse_allowances(csv, "allowances.csv")

    assert result.errors == []
    assert len(result.rows) == 2
    assert result.rows[0].year == 2020
    assert result.rows[0].total_days == 20
    assert result.rows[1].total_days == 15


def test_parse_allowances_missing_metadata_fails_whole_file() -> None:
    csv = b"Employee,Total vacation days\nuser1@example.com,20\n"

    with pytest.raises(ImportStructureError, match="metadata"):
        parse_allowances(csv, "allowances.csv")


def test_parse_allowances_invalid_days_are_row_errors() -> None:
    csv = (
        b"Vacation year,2019\n"
        b"Employee,Total vacation days\n"
        b"user1@example.com,abc\n"
        b"user2@example.com,10\n"
    )

    result = parse_allowances(csv, "allowances.csv")

    assert len(result.rows) == 1
    assert result.rows[0].email == "user2@example.com"
    assert len(result.errors) == 1


def test_parse_usages_happy_path() -> None:
    csv = (
        b"Employee,Vacation start date,Vacation end date\n"
        b'user1@example.com,"Friday, August 30, 2019","Wednesday, September 11, 2019"\n'
    )

    result = parse_usages(csv, "usages.csv")

    assert result.errors == []
    assert len(result.rows) == 1
    assert result.rows[0].start_date == date(2019, 8, 30)
    assert result.rows[0].end_date == date(2019, 9, 11)


def test_parse_usages_start_after_end_is_row_error() -> None:
    csv = (
        b"Employee,Vacation start date,Vacation end date\n"
        b"user1@example.com,2019-09-11,2019-08-30\n"
    )

    result = parse_usages(csv, "usages.csv")

    assert result.rows == []
    assert len(result.errors) == 1
    assert "after end date" in result.errors[0].message


def test_unsupported_extension_fails_whole_file() -> None:
    with pytest.raises(ImportStructureError, match="Unsupported file extension"):
        parse_employees(b"anything", "employees.txt")
