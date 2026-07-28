"""Vacation date string parsing."""

from datetime import date, datetime

from vacation_tracker.core.constants import VACATION_DATE_FORMATS


def parse_vacation_date(value: str) -> date:
    """Parse a vacation date string using known formats.

    Raises:
        ValueError: If no format matches.
    """
    text = value.strip()
    if not text:
        raise ValueError("Date value is empty")

    for fmt in VACATION_DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue

    raise ValueError(f"Unrecognized date format: {value!r}")
