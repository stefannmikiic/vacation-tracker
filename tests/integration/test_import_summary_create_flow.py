"""HTTP integration: import → summary → create usage."""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.factories import create_allowance, create_employee
from vacation_tracker.core.constants import UserRole


@pytest.fixture
def integration_session(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> Session:
    """Flush instead of commit so the shared rollback fixture still cleans up."""
    monkeypatch.setattr(db_session, "commit", db_session.flush)
    return db_session


def _upload(
    client: TestClient,
    path: str,
    *,
    filename: str,
    content: bytes,
    auth: tuple[str, str],
):
    return client.post(
        path,
        files={"file": (filename, content, "text/csv")},
        auth=auth,
    )


def test_import_summary_create_usage_happy_path(
    api_client: TestClient,
    integration_session: Session,
) -> None:
    admin, admin_password = create_employee(
        integration_session,
        role=UserRole.ADMIN.value,
    )
    admin_auth = (admin.email, admin_password)

    email = f"flow-{uuid4()}@example.com"
    password = "FlowSecret1!"

    employees_csv = (
        b"Employee Email,Employee Password\n" + f"{email},{password}\n".encode()
    )
    allowances_csv = (
        b"Vacation year,2021\nEmployee,Total vacation days\n" + f"{email},10\n".encode()
    )

    emp_import = _upload(
        api_client,
        "/api/v1/admin/imports/employees",
        filename="employees.csv",
        content=employees_csv,
        auth=admin_auth,
    )
    assert emp_import.status_code == 200
    assert emp_import.json()["created"] == 1
    assert emp_import.json()["failed"] == 0

    allw_import = _upload(
        api_client,
        "/api/v1/admin/imports/allowances",
        filename="allowances.csv",
        content=allowances_csv,
        auth=admin_auth,
    )
    assert allw_import.status_code == 200
    assert allw_import.json()["created"] == 1
    assert allw_import.json()["failed"] == 0

    employee_auth = (email, password)

    summary_before = api_client.get(
        "/api/v1/me/vacations/summary",
        params={"year": 2021},
        auth=employee_auth,
    )
    assert summary_before.status_code == 200
    assert summary_before.json() == {
        "year": 2021,
        "total_days": 10,
        "used_days": 0,
        "available_days": 10,
    }

    create_response = api_client.post(
        "/api/v1/me/vacations/usages",
        json={"start_date": "2021-07-01", "end_date": "2021-07-03"},
        auth=employee_auth,
    )
    assert create_response.status_code == 201
    assert create_response.json()["start_date"] == "2021-07-01"
    assert create_response.json()["end_date"] == "2021-07-03"

    summary_after = api_client.get(
        "/api/v1/me/vacations/summary",
        params={"year": 2021},
        auth=employee_auth,
    )
    assert summary_after.status_code == 200
    assert summary_after.json() == {
        "year": 2021,
        "total_days": 10,
        "used_days": 3,
        "available_days": 7,
    }


def test_create_usage_exceeding_balance_returns_400(
    api_client: TestClient,
    integration_session: Session,
) -> None:
    employee, password = create_employee(integration_session)
    create_allowance(integration_session, employee.id, 2021, 2)

    response = api_client.post(
        "/api/v1/me/vacations/usages",
        json={"start_date": "2021-06-01", "end_date": "2021-06-05"},
        auth=(employee.email, password),
    )

    assert response.status_code == 400
    assert "Insufficient" in response.json()["detail"]
