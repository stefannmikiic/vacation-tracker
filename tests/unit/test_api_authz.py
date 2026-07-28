"""API authorization boundary tests."""

from collections.abc import Generator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from vacation_tracker.core.constants import UserRole
from vacation_tracker.core.security import hash_password
from vacation_tracker.db.models import Employee, VacationAllowance
from vacation_tracker.db.session import get_db
from vacation_tracker.main import create_app


@pytest.fixture
def api_client(db_session: Session) -> Generator[TestClient, None, None]:
    """Real app with DB dependency overridden to the rolled-back test session."""
    app = create_app()

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client


def _create_user(
    session: Session,
    *,
    role: str = UserRole.EMPLOYEE.value,
    password: str = "Secret123!",
) -> tuple[Employee, str]:
    employee = Employee(
        email=f"api-{uuid4()}@example.com",
        password_hash=hash_password(password),
        role=role,
        is_active=True,
    )
    session.add(employee)
    session.flush()
    return employee, password


def test_employee_cannot_access_admin_employees(
    api_client: TestClient,
    db_session: Session,
) -> None:
    employee, password = _create_user(db_session)

    response = api_client.get(
        "/api/v1/admin/employees",
        auth=(employee.email, password),
    )

    assert response.status_code == 403


def test_employee_cannot_access_other_employee_allowances(
    api_client: TestClient,
    db_session: Session,
) -> None:
    employee, password = _create_user(db_session)
    other, _ = _create_user(db_session)

    response = api_client.get(
        f"/api/v1/admin/employees/{other.id}/allowances",
        auth=(employee.email, password),
    )

    assert response.status_code == 403


def test_admin_can_list_employees(
    api_client: TestClient,
    db_session: Session,
) -> None:
    admin, password = _create_user(db_session, role=UserRole.ADMIN.value)
    _create_user(db_session)

    response = api_client.get(
        "/api/v1/admin/employees",
        auth=(admin.email, password),
    )

    assert response.status_code == 200
    emails = {row["email"] for row in response.json()}
    assert admin.email in emails


def test_admin_can_view_employee_allowances(
    api_client: TestClient,
    db_session: Session,
) -> None:
    admin, password = _create_user(db_session, role=UserRole.ADMIN.value)
    employee, _ = _create_user(db_session)
    db_session.add(VacationAllowance(employee_id=employee.id, year=2021, total_days=20))
    db_session.flush()

    response = api_client.get(
        f"/api/v1/admin/employees/{employee.id}/allowances",
        auth=(admin.email, password),
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["year"] == 2021
    assert payload[0]["total_days"] == 20


def test_employee_summary_returns_own_balance(
    api_client: TestClient,
    db_session: Session,
) -> None:
    employee, password = _create_user(db_session)
    db_session.add(VacationAllowance(employee_id=employee.id, year=2021, total_days=20))
    db_session.flush()

    response = api_client.get(
        "/api/v1/me/vacations/summary",
        params={"year": 2021},
        auth=(employee.email, password),
    )

    assert response.status_code == 200
    assert response.json() == {
        "year": 2021,
        "total_days": 20,
        "used_days": 0,
        "available_days": 20,
    }


def test_employee_can_create_own_usage(
    api_client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # create_usage commits; flush keeps the shared rollback fixture effective.
    monkeypatch.setattr(db_session, "commit", db_session.flush)

    employee, password = _create_user(db_session)
    db_session.add(VacationAllowance(employee_id=employee.id, year=2021, total_days=10))
    db_session.flush()

    response = api_client.post(
        "/api/v1/me/vacations/usages",
        json={"start_date": "2021-07-01", "end_date": "2021-07-03"},
        auth=(employee.email, password),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["employee_id"] == str(employee.id)
    assert body["start_date"] == "2021-07-01"
    assert body["end_date"] == "2021-07-03"
