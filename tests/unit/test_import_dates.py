"""Unit tests for vacation date parsing."""

from datetime import date

import pytest

from vacation_tracker.imports.dates import parse_vacation_date


def test_parse_english_long_date() -> None:
    assert parse_vacation_date("Friday, August 30, 2019") == date(2019, 8, 30)


def test_parse_iso_date() -> None:
    assert parse_vacation_date("2019-08-30") == date(2019, 8, 30)


def test_parse_empty_date_raises() -> None:
    with pytest.raises(ValueError, match="empty"):
        parse_vacation_date("   ")


def test_parse_unrecognized_date_raises() -> None:
    with pytest.raises(ValueError, match="Unrecognized"):
        parse_vacation_date("30/08/2019")
