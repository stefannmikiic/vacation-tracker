"""Create or update the bootstrap admin user.

Usage:
    uv run python scripts/create_admin.py

Requires environment variables (e.g. via .env loaded by the process, or exported):
    ADMIN_EMAIL
    ADMIN_PASSWORD

Also requires DATABASE_URL for the DB connection (via Settings).
"""

import os
import sys

from sqlalchemy import select

from vacation_tracker.core.constants import UserRole
from vacation_tracker.core.logging import get_logger, setup_logging
from vacation_tracker.core.security import hash_password
from vacation_tracker.db.models import Employee
from vacation_tracker.db.session import SessionLocal

logger = get_logger(__name__)


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or not value.strip():
        logger.error("Missing required environment variable: %s", name)
        sys.exit(1)
    return value.strip()


def create_or_update_admin() -> None:
    email = _require_env("ADMIN_EMAIL").lower()
    password = _require_env("ADMIN_PASSWORD")
    password_hash = hash_password(password)

    with SessionLocal() as session:
        employee = session.scalar(select(Employee).where(Employee.email == email))

        if employee is None:
            employee = Employee(
                email=email,
                password_hash=password_hash,
                role=UserRole.ADMIN.value,
                is_active=True,
            )
            session.add(employee)
            action = "created"
        else:
            employee.password_hash = password_hash
            employee.role = UserRole.ADMIN.value
            employee.is_active = True
            action = "updated"

        session.commit()
        logger.info("Admin user %s: %s (id=%s)", action, email, employee.id)


if __name__ == "__main__":
    setup_logging()
    # Load .env into the process so ADMIN_* are available to os.getenv.
    from dotenv import load_dotenv

    load_dotenv()
    create_or_update_admin()
