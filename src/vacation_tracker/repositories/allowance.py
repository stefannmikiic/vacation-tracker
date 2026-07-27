"""Vacation allowance persistence queries."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from vacation_tracker.db.models import VacationAllowance
from vacation_tracker.repositories.base import BaseRepository


class AllowanceRepository(BaseRepository[VacationAllowance]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, VacationAllowance)

    def get_for_employee_year(
        self,
        employee_id: uuid.UUID,
        year: int,
    ) -> VacationAllowance | None:
        stmt = select(VacationAllowance).where(
            VacationAllowance.employee_id == employee_id,
            VacationAllowance.year == year,
        )
        return self._session.scalar(stmt)

    def upsert(
        self,
        employee_id: uuid.UUID,
        year: int,
        total_days: int,
    ) -> VacationAllowance:
        """Create or update the allowance for an employee/year."""
        allowance = self.get_for_employee_year(employee_id, year)
        if allowance is None:
            allowance = VacationAllowance(
                employee_id=employee_id,
                year=year,
                total_days=total_days,
            )
            self.add(allowance)
        else:
            allowance.total_days = total_days
        return allowance
