"""Shared pytest fixtures."""

from collections.abc import Generator

import pytest
from sqlalchemy.orm import Session

from vacation_tracker.db.session import SessionLocal


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Provide a DB session that rolls back after each test."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
