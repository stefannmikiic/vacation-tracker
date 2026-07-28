"""Employee test factory."""

from uuid import uuid4

from sqlalchemy.orm import Session

from vacation_tracker.core.constants import UserRole
from vacation_tracker.core.security import hash_password
from vacation_tracker.db.models import Employee


def create_employee(
    session: Session,
    *,
    email: str | None = None,
    password: str = "Secret123!",
    role: str = UserRole.EMPLOYEE.value,
    is_active: bool = True,
) -> tuple[Employee, str]:
    """Persist an employee and return ``(employee, plaintext_password)``."""
    employee = Employee(
        email=email or f"user-{uuid4()}@example.com",
        password_hash=hash_password(password),
        role=role,
        is_active=is_active,
    )
    session.add(employee)
    session.flush()
    return employee, password
