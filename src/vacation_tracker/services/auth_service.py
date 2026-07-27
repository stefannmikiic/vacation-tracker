"""Authentication use-cases."""

from __future__ import annotations

from sqlalchemy.orm import Session

from vacation_tracker.core.security import verify_password
from vacation_tracker.db.models import Employee
from vacation_tracker.repositories import EmployeeRepository


class AuthService:
    def __init__(self, session: Session) -> None:
        self._employees = EmployeeRepository(session)

    def authenticate(self, email: str, password: str) -> Employee | None:
        """Return the employee if credentials are valid and the account is active."""
        employee = self._employees.get_by_email(email)
        if employee is None or not employee.is_active:
            return None
        if not verify_password(password, employee.password_hash):
            return None
        return employee
