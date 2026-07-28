"""Vacation use-cases: summary, list usages, create usage."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from vacation_tracker.core.exceptions import (
    InsufficientBalanceError,
    MissingAllowanceError,
    OverlappingUsageError,
)
from vacation_tracker.db.models import VacationUsage
from vacation_tracker.repositories import AllowanceRepository, UsageRepository
from vacation_tracker.services.day_counting import days_in_year, split_days_by_year


@dataclass(frozen=True)
class VacationSummary:
    """Yearly vacation balance for one employee."""

    year: int
    total_days: int
    used_days: int
    available_days: int


class VacationService:
    """Employee vacation queries and create rules."""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._allowances = AllowanceRepository(session)
        self._usages = UsageRepository(session)

    def get_summary(self, employee_id: uuid.UUID, year: int) -> VacationSummary:
        """Return total / used / available days for a calendar year."""
        allowance = self._allowances.get_for_employee_year(employee_id, year)
        total_days = 0 if allowance is None else allowance.total_days
        used_days = self._used_days_for_year(employee_id, year)
        # Never expose negative available (e.g. imported usages without allowance).
        available_days = max(0, total_days - used_days)
        return VacationSummary(
            year=year,
            total_days=total_days,
            used_days=used_days,
            available_days=available_days,
        )

    def list_usages(
        self,
        employee_id: uuid.UUID,
        start: date,
        end: date,
    ) -> list[VacationUsage]:
        """List usages that overlap the inclusive [start, end] window."""
        if end < start:
            raise ValueError("end date must be on or after start date")
        return self._usages.list_for_range(employee_id, start, end)

    def create_usage(
        self,
        employee_id: uuid.UUID,
        start: date,
        end: date,
    ) -> VacationUsage:
        """Create a usage after overlap and balance checks."""
        if end < start:
            raise ValueError("end date must be on or after start date")

        overlapping = self._usages.find_overlapping(employee_id, start, end)
        if overlapping:
            raise OverlappingUsageError(
                f"Usage {start}–{end} overlaps an existing vacation period"
            )

        days_by_year = split_days_by_year(start, end)
        for year, days_needed in days_by_year.items():
            allowance = self._allowances.get_for_employee_year(employee_id, year)
            if allowance is None:
                raise MissingAllowanceError(
                    f"No vacation allowance found for year {year}"
                )

            used_days = self._used_days_for_year(employee_id, year)
            available = allowance.total_days - used_days
            if days_needed > available:
                raise InsufficientBalanceError(
                    f"Insufficient vacation balance for {year}: "
                    f"need {days_needed}, available {available}"
                )

        try:
            usage = VacationUsage(
                employee_id=employee_id,
                start_date=start,
                end_date=end,
            )
            self._usages.add(usage)
            self._session.commit()
            return usage
        except Exception:
            self._session.rollback()
            raise

    def _used_days_for_year(self, employee_id: uuid.UUID, year: int) -> int:
        year_start = date(year, 1, 1)
        year_end = date(year, 12, 31)
        usages = self._usages.list_for_range(employee_id, year_start, year_end)
        return sum(
            days_in_year(usage.start_date, usage.end_date, year) for usage in usages
        )
