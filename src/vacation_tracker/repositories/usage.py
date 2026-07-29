"""Vacation usage persistence queries."""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from vacation_tracker.db.models import VacationUsage
from vacation_tracker.repositories.base import BaseRepository


class UsageRepository(BaseRepository[VacationUsage]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, VacationUsage)

    def list_for_range(
        self,
        employee_id: uuid.UUID,
        start: date,
        end: date,
    ) -> list[VacationUsage]:
        """Return usages that overlap the inclusive [start, end] window."""
        stmt = (
            select(VacationUsage)
            .where(
                VacationUsage.employee_id == employee_id,
                VacationUsage.start_date <= end,
                VacationUsage.end_date >= start,
            )
            .order_by(VacationUsage.start_date)
        )
        return list(self._session.scalars(stmt))

    def find_overlapping(
        self,
        employee_id: uuid.UUID,
        start: date,
        end: date,
        *,
        exclude_id: uuid.UUID | None = None,
    ) -> list[VacationUsage]:
        """Return usages for the employee that overlap [start, end]."""
        stmt = select(VacationUsage).where(
            VacationUsage.employee_id == employee_id,
            VacationUsage.start_date <= end,
            VacationUsage.end_date >= start,
        )
        if exclude_id is not None:
            stmt = stmt.where(VacationUsage.id != exclude_id)
        return list(self._session.scalars(stmt))

    def list_filtered(
        self,
        *,
        employee_id: uuid.UUID | None = None,
        window_start: date | None = None,
        window_end: date | None = None,
        limit: int,
        offset: int = 0,
    ) -> list[VacationUsage]:
        """Return usages matching optional employee and date-window filters."""
        stmt = select(VacationUsage)
        if employee_id is not None:
            stmt = stmt.where(VacationUsage.employee_id == employee_id)
        if window_start is not None and window_end is not None:
            stmt = stmt.where(
                VacationUsage.start_date <= window_end,
                VacationUsage.end_date >= window_start,
            )
        stmt = stmt.order_by(VacationUsage.start_date).offset(offset).limit(limit)
        return list(self._session.scalars(stmt))
