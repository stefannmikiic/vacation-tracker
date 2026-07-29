"""ImportService happy/failure path tests (Postgres, rolled back)."""

from collections.abc import Generator
from datetime import date
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from vacation_tracker.core.constants import UserRole
from vacation_tracker.core.security import hash_password, verify_password
from vacation_tracker.db.models import Employee, VacationUsage
from vacation_tracker.repositories import AllowanceRepository, EmployeeRepository
from vacation_tracker.services.import_service import ImportService


@pytest.fixture
def import_session(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[Session, None, None]:
    """Use flush instead of commit so the shared rollback fixture still cleans up."""
    monkeypatch.setattr(db_session, "commit", db_session.flush)
    yield db_session


def _unique_email(prefix: str = "imp") -> str:
    return f"{prefix}-{uuid4()}@example.com"


def test_import_employees_creates_and_updates_password(
    import_session: Session,
) -> None:
    email = _unique_email("emp")
    existing = Employee(
        email=email,
        password_hash=hash_password("OldSecret!"),
        role=UserRole.EMPLOYEE.value,
        is_active=True,
    )
    import_session.add(existing)
    import_session.flush()

    csv = (
        "Employee Email,Employee Password\n"
        f"{email},NewSecret!\n"
        f"{_unique_email('new')},BrandNew!\n"
    ).encode()

    summary = ImportService(import_session).import_employees(csv, "employees.csv")

    assert summary.created == 1
    assert summary.updated == 1
    assert summary.failed == 0

    repo = EmployeeRepository(import_session)
    updated = repo.get_by_email(email)
    assert updated is not None
    assert updated.role == UserRole.EMPLOYEE.value
    assert verify_password("NewSecret!", updated.password_hash)

def test_import_employees_refuses_admin_password_update(
    import_session: Session,
) -> None:
    email = _unique_email("admin")
    existing = Employee(
        email=email,
        password_hash=hash_password("OldSecret!"),
        role=UserRole.ADMIN.value,
        is_active=True,
    )
    import_session.add(existing)
    import_session.flush()

    csv = (
        "Employee Email,Employee Password\n"
        f"{email},NewSecret!\n"
    ).encode()

    summary = ImportService(import_session).import_employees(csv, "employees.csv")

    assert summary.created == 0
    assert summary.updated == 0
    assert summary.failed == 1
    assert any(
        "Cannot update admin via import" in err.message
        for err in summary.errors
    )

    admin = EmployeeRepository(import_session).get_by_email(email)
    assert admin is not None
    assert admin.role == UserRole.ADMIN.value
    assert verify_password("OldSecret!", admin.password_hash)
    assert not verify_password("NewSecret!", admin.password_hash)

def test_import_allowances_upserts_and_rejects_unknown_employee(
    import_session: Session,
) -> None:
    email = _unique_email("allw")
    import_session.add(
        Employee(
            email=email,
            password_hash=hash_password("Secret1!"),
            role=UserRole.EMPLOYEE.value,
        )
    )
    import_session.flush()

    unknown = _unique_email("missing")
    csv = (
        f"Vacation year,2021\nEmployee,Total vacation days\n{email},20\n{unknown},10\n"
    ).encode()

    service = ImportService(import_session)
    first = service.import_allowances(csv, "allowances.csv")
    assert first.created == 1
    assert first.updated == 0
    assert first.failed == 1
    assert any(unknown in err.message for err in first.errors)

    second_csv = (
        f"Vacation year,2021\nEmployee,Total vacation days\n{email},25\n"
    ).encode()
    second = service.import_allowances(second_csv, "allowances.csv")
    assert second.created == 0
    assert second.updated == 1

    employee = EmployeeRepository(import_session).get_by_email(email)
    assert employee is not None
    allowance = AllowanceRepository(import_session).get_for_employee_year(
        employee.id,
        2021,
    )
    assert allowance is not None
    assert allowance.total_days == 25


def test_import_usages_creates_and_rejects_overlap(
    import_session: Session,
) -> None:
    email = _unique_email("usage")
    employee = Employee(
        email=email,
        password_hash=hash_password("Secret1!"),
        role=UserRole.EMPLOYEE.value,
    )
    import_session.add(employee)
    import_session.flush()

    csv = (
        "Employee,Vacation start date,Vacation end date\n"
        f"{email},2021-06-01,2021-06-05\n"
        f"{email},2021-06-03,2021-06-07\n"
        f"{email},2021-08-01,2021-08-02\n"
    ).encode()

    summary = ImportService(import_session).import_usages(csv, "usages.csv")

    assert summary.created == 2
    assert summary.updated == 0
    assert summary.failed == 1
    assert any("Overlapping" in err.message for err in summary.errors)

    usages = list(
        import_session.scalars(
            select(VacationUsage).where(VacationUsage.employee_id == employee.id)
        )
    )
    assert len(usages) == 2
    starts = {usage.start_date for usage in usages}
    assert starts == {date(2021, 6, 1), date(2021, 8, 1)}

def test_import_employees_handles_duplicate_rows(
    import_session: Session,
) -> None:
    email = _unique_email("duplicate")

    csv = (
        "Employee Email,Employee Password\n"
        f"{email},Password1!\n"
        f"{email},Password2!\n"
    ).encode()

    summary = ImportService(
        import_session
    ).import_employees(
        csv,
        "employees.csv",
    )

    assert summary.created == 1
    assert summary.failed == 0