"""Shared pytest fixtures."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from vacation_tracker.db.session import SessionLocal, get_db
from vacation_tracker.main import create_app


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Provide a DB session that rolls back after each test."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def api_client(db_session: Session) -> Generator[TestClient, None, None]:
    """Real app with DB dependency overridden to the rolled-back test session."""
    app = create_app()

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
