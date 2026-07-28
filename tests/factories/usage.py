"""Vacation usage test factory."""

import uuid
from datetime import date

from sqlalchemy.orm import Session

from vacation_tracker.db.models import VacationUsage


def create_usage(
    session: Session,
    employee_id: uuid.UUID,
    start: date,
    end: date,
) -> VacationUsage:
    """Persist a used-vacation date range for an employee."""
    usage = VacationUsage(
        employee_id=employee_id,
        start_date=start,
        end_date=end,
    )
    session.add(usage)
    session.flush()
    return usage
