"""Vacation allowance test factory."""

import uuid

from sqlalchemy.orm import Session

from vacation_tracker.db.models import VacationAllowance


def create_allowance(
    session: Session,
    employee_id: uuid.UUID,
    year: int,
    total_days: int,
) -> VacationAllowance:
    """Persist a yearly allowance for an employee."""
    allowance = VacationAllowance(
        employee_id=employee_id,
        year=year,
        total_days=total_days,
    )
    session.add(allowance)
    session.flush()
    return allowance
