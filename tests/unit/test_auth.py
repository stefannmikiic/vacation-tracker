"""Tests for AuthService and Basic Auth / role dependencies."""

from collections.abc import Generator
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from vacation_tracker.api.deps import AdminUser, CurrentUser
from vacation_tracker.core.constants import UserRole
from vacation_tracker.core.security import hash_password, verify_password
from vacation_tracker.db.models import Employee
from vacation_tracker.db.session import get_db
from vacation_tracker.services.auth_service import AuthService


def _create_user(
    session: Session,
    *,
    email: str | None = None,
    password: str = "Secret123!",
    role: str = UserRole.EMPLOYEE.value,
    is_active: bool = True,
) -> tuple[Employee, str]:
    plain = password
    employee = Employee(
        email=email or f"user-{uuid4()}@example.com",
        password_hash=hash_password(plain),
        role=role,
        is_active=is_active,
    )
    session.add(employee)
    session.flush()
    return employee, plain


def test_verify_password_roundtrip() -> None:
    hashed = hash_password("plain-secret")
    assert verify_password("plain-secret", hashed)
    assert not verify_password("wrong", hashed)


def test_authenticate_success(db_session: Session) -> None:
    employee, password = _create_user(db_session)
    result = AuthService(db_session).authenticate(employee.email, password)
    assert result is not None
    assert result.id == employee.id


def test_authenticate_wrong_password(db_session: Session) -> None:
    employee, _ = _create_user(db_session)
    assert AuthService(db_session).authenticate(employee.email, "nope") is None


def test_authenticate_unknown_email(db_session: Session) -> None:
    assert AuthService(db_session).authenticate("missing@example.com", "x") is None


def test_authenticate_inactive_user(db_session: Session) -> None:
    employee, password = _create_user(db_session, is_active=False)
    assert AuthService(db_session).authenticate(employee.email, password) is None


@pytest.fixture
def auth_client(db_session: Session) -> Generator[TestClient, None, None]:
    """Minimal app exposing CurrentUser / AdminUser for dependency tests."""
    app = FastAPI()

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    @app.get("/me")
    def me(user: CurrentUser) -> dict[str, str]:
        return {"email": user.email, "role": user.role}

    @app.get("/admin-only")
    def admin_only(_admin: AdminUser) -> dict[str, bool]:
        return {"ok": True}

    with TestClient(app) as client:
        yield client


def test_basic_auth_success(auth_client: TestClient, db_session: Session) -> None:
    employee, password = _create_user(db_session)
    response = auth_client.get("/me", auth=(employee.email, password))
    assert response.status_code == 200
    assert response.json()["email"] == employee.email


def test_basic_auth_failure(auth_client: TestClient, db_session: Session) -> None:
    employee, _ = _create_user(db_session)
    response = auth_client.get("/me", auth=(employee.email, "wrong"))
    assert response.status_code == 401
    assert response.headers.get("www-authenticate", "").lower().startswith("basic")


def test_admin_allowed(auth_client: TestClient, db_session: Session) -> None:
    admin, password = _create_user(db_session, role=UserRole.ADMIN.value)
    response = auth_client.get("/admin-only", auth=(admin.email, password))
    assert response.status_code == 200


def test_admin_forbidden_for_employee(
    auth_client: TestClient,
    db_session: Session,
) -> None:
    employee, password = _create_user(db_session, role=UserRole.EMPLOYEE.value)
    response = auth_client.get("/admin-only", auth=(employee.email, password))
    assert response.status_code == 403
