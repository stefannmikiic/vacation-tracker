"""Employee persistence queries."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from vacation_tracker.db.models import Employee
from vacation_tracker.repositories.base import BaseRepository


class EmployeeRepository(BaseRepository[Employee]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Employee)

    def get_by_email(self, email: str) -> Employee | None:
        stmt = select(Employee).where(Employee.email == email.lower())
        return self._session.scalar(stmt)

    def list(self, *, limit: int, offset: int = 0) -> list[Employee]:
        """Return employees ordered by email, with simple limit/offset."""
        stmt = select(Employee).order_by(Employee.email).offset(offset).limit(limit)
        return list(self._session.scalars(stmt))
