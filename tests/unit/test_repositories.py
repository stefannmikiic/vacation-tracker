"""Repository tests against a real Postgres session (rolled back)."""

from datetime import date
from uuid import uuid4

from sqlalchemy.orm import Session

from vacation_tracker.core.constants import UserRole
from vacation_tracker.db.models import Employee, VacationUsage
from vacation_tracker.repositories import (
    AllowanceRepository,
    EmployeeRepository,
    UsageRepository,
)


def _make_employee(session: Session, email: str | None = None) -> Employee:
    employee = Employee(
        email=email or f"test-{uuid4()}@example.com",
        password_hash="not-a-real-hash",
        role=UserRole.EMPLOYEE.value,
        is_active=True,
    )
    session.add(employee)
    session.flush()
    return employee


def test_employee_get_by_email(db_session: Session) -> None:
    repo = EmployeeRepository(db_session)
    employee = _make_employee(db_session, email="user.one@example.com")

    found = repo.get_by_email("User.One@Example.com")

    assert found is not None
    assert found.id == employee.id


def test_employee_get_by_id(db_session: Session) -> None:
    repo = EmployeeRepository(db_session)
    employee = _make_employee(db_session)

    assert repo.get_by_id(employee.id) is employee
    assert repo.get_by_id(uuid4()) is None


def test_allowance_upsert(db_session: Session) -> None:
    employee = _make_employee(db_session)
    repo = AllowanceRepository(db_session)

    created = repo.upsert(employee.id, 2021, 20)
    db_session.flush()
    assert created.total_days == 20

    updated = repo.upsert(employee.id, 2021, 25)
    db_session.flush()
    assert updated.id == created.id
    assert updated.total_days == 25
    assert repo.get_for_employee_year(employee.id, 2021) is updated


def test_usage_list_for_range_and_overlap(db_session: Session) -> None:
    employee = _make_employee(db_session)
    repo = UsageRepository(db_session)

    june = VacationUsage(
        employee_id=employee.id,
        start_date=date(2021, 6, 1),
        end_date=date(2021, 6, 5),
    )
    august = VacationUsage(
        employee_id=employee.id,
        start_date=date(2021, 8, 10),
        end_date=date(2021, 8, 12),
    )
    repo.add(june)
    repo.add(august)
    db_session.flush()

    in_summer = repo.list_for_range(employee.id, date(2021, 6, 1), date(2021, 8, 31))
    assert [u.id for u in in_summer] == [june.id, august.id]

    overlapping = repo.find_overlapping(
        employee.id,
        date(2021, 6, 3),
        date(2021, 6, 10),
    )
    assert [u.id for u in overlapping] == [june.id]

    excluding = repo.find_overlapping(
        employee.id,
        date(2021, 6, 3),
        date(2021, 6, 10),
        exclude_id=june.id,
    )
    assert excluding == []
