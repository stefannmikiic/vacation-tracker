"""API authorization boundary tests."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.factories import create_allowance, create_employee
from vacation_tracker.core.constants import UserRole


def test_employee_cannot_access_admin_employees(
    api_client: TestClient,
    db_session: Session,
) -> None:
    employee, password = create_employee(db_session)

    response = api_client.get(
        "/api/v1/admin/employees",
        auth=(employee.email, password),
    )

    assert response.status_code == 403


def test_employee_cannot_access_other_employee_allowances(
    api_client: TestClient,
    db_session: Session,
) -> None:
    employee, password = create_employee(db_session)
    other, _ = create_employee(db_session)

    response = api_client.get(
        f"/api/v1/admin/employees/{other.id}/allowances",
        auth=(employee.email, password),
    )

    assert response.status_code == 403


def test_admin_can_list_employees(
    api_client: TestClient,
    db_session: Session,
) -> None:
    admin, password = create_employee(db_session, role=UserRole.ADMIN.value)
    create_employee(db_session)

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
    admin, password = create_employee(db_session, role=UserRole.ADMIN.value)
    employee, _ = create_employee(db_session)
    create_allowance(db_session, employee.id, 2021, 20)

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
    employee, password = create_employee(db_session)
    create_allowance(db_session, employee.id, 2021, 20)

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

    employee, password = create_employee(db_session)
    create_allowance(db_session, employee.id, 2021, 10)

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
