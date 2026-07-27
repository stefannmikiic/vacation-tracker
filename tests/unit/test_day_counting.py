"""Unit tests for vacation day-counting helpers."""

from datetime import date

import pytest

from vacation_tracker.services.day_counting import (
    days_in_year,
    inclusive_day_count,
    split_days_by_year,
)


def test_inclusive_single_day() -> None:
    assert inclusive_day_count(date(2021, 1, 1), date(2021, 1, 1)) == 1


def test_inclusive_multi_day() -> None:
    # Matches sample: Mon May 25 – Thu May 28, 2020
    assert inclusive_day_count(date(2020, 5, 25), date(2020, 5, 28)) == 4


def test_inclusive_rejects_inverted_range() -> None:
    with pytest.raises(ValueError, match="end date"):
        inclusive_day_count(date(2021, 1, 2), date(2021, 1, 1))


def test_days_in_year_fully_inside() -> None:
    assert days_in_year(date(2021, 6, 1), date(2021, 6, 10), 2021) == 10


def test_days_in_year_cross_year_split() -> None:
    start = date(2020, 12, 28)
    end = date(2021, 1, 3)
    assert days_in_year(start, end, 2020) == 4  # Dec 28–31
    assert days_in_year(start, end, 2021) == 3  # Jan 1–3
    assert days_in_year(start, end, 2019) == 0


def test_split_days_by_year() -> None:
    assert split_days_by_year(date(2020, 12, 28), date(2021, 1, 3)) == {
        2020: 4,
        2021: 3,
    }


def test_split_days_same_year() -> None:
    assert split_days_by_year(date(2021, 3, 1), date(2021, 3, 5)) == {2021: 5}
