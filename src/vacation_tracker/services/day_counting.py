"""Vacation day-counting helpers (pure functions, no I/O).

Locked rules:
- Inclusive calendar days: (end - start).days + 1
- Cross-year ranges: each calendar day counts toward the year it falls in
"""

from __future__ import annotations

from datetime import date


def inclusive_day_count(start: date, end: date) -> int:
    """Return the number of inclusive calendar days in [start, end]."""
    if end < start:
        raise ValueError("end date must be on or after start date")
    return (end - start).days + 1


def days_in_year(start: date, end: date, year: int) -> int:
    """Return how many inclusive days of [start, end] fall in ``year``."""
    if end < start:
        raise ValueError("end date must be on or after start date")

    year_start = date(year, 1, 1)
    year_end = date(year, 12, 31)

    overlap_start = max(start, year_start)
    overlap_end = min(end, year_end)

    if overlap_end < overlap_start:
        return 0
    return inclusive_day_count(overlap_start, overlap_end)


def split_days_by_year(start: date, end: date) -> dict[int, int]:
    """Split [start, end] into ``{year: day_count}`` for each touched year."""
    if end < start:
        raise ValueError("end date must be on or after start date")

    counts: dict[int, int] = {}
    for year in range(start.year, end.year + 1):
        count = days_in_year(start, end, year)
        if count:
            counts[year] = count
    return counts
