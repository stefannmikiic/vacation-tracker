"""Focused unit tests for VacationService."""

from collections.abc import Generator
from datetime import date

import pytest
from sqlalchemy.orm import Session

from tests.factories import create_allowance, create_employee, create_usage
from vacation_tracker.core.exceptions import (
    InsufficientBalanceError,
    MissingAllowanceError,
    OverlappingUsageError,
)
from vacation_tracker.services.vacation_service import VacationService


@pytest.fixture
def vacation_session(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[Session, None, None]:
    """Use flush instead of commit so the shared rollback fixture still cleans up."""
    monkeypatch.setattr(db_session, "commit", db_session.flush)
    yield db_session


def test_get_summary_calculates_balance(vacation_session: Session) -> None:
    employee, _ = create_employee(vacation_session)
    create_allowance(vacation_session, employee.id, 2021, 20)
    create_usage(vacation_session, employee.id, date(2021, 6, 1), date(2021, 6, 5))

    summary = VacationService(vacation_session).get_summary(employee.id, 2021)

    assert summary.year == 2021
    assert summary.total_days == 20
    assert summary.used_days == 5
    assert summary.available_days == 15


def test_get_summary_missing_allowance_is_zero_not_negative(
    vacation_session: Session,
) -> None:
    employee, _ = create_employee(vacation_session)
    create_usage(vacation_session, employee.id, date(2021, 6, 1), date(2021, 6, 5))

    summary = VacationService(vacation_session).get_summary(employee.id, 2021)

    assert summary.total_days == 0
    assert summary.used_days == 5
    assert summary.available_days == 0


def test_get_summary_splits_cross_year_usage(vacation_session: Session) -> None:
    employee, _ = create_employee(vacation_session)
    create_allowance(vacation_session, employee.id, 2020, 20)
    create_allowance(vacation_session, employee.id, 2021, 20)
    # Dec 30–31 2020 (2 days) + Jan 1–2 2021 (2 days)
    create_usage(vacation_session, employee.id, date(2020, 12, 30), date(2021, 1, 2))

    service = VacationService(vacation_session)
    summary_2020 = service.get_summary(employee.id, 2020)
    summary_2021 = service.get_summary(employee.id, 2021)

    assert summary_2020.used_days == 2
    assert summary_2021.used_days == 2


def test_create_usage_success(vacation_session: Session) -> None:
    employee, _ = create_employee(vacation_session)
    create_allowance(vacation_session, employee.id, 2021, 10)

    usage = VacationService(vacation_session).create_usage(
        employee.id,
        date(2021, 7, 1),
        date(2021, 7, 3),
    )

    assert usage.start_date == date(2021, 7, 1)
    assert usage.end_date == date(2021, 7, 3)
    summary = VacationService(vacation_session).get_summary(employee.id, 2021)
    assert summary.used_days == 3
    assert summary.available_days == 7


def test_create_usage_rejects_overlap(vacation_session: Session) -> None:
    employee, _ = create_employee(vacation_session)
    create_allowance(vacation_session, employee.id, 2021, 20)
    create_usage(vacation_session, employee.id, date(2021, 6, 1), date(2021, 6, 5))

    with pytest.raises(OverlappingUsageError):
        VacationService(vacation_session).create_usage(
            employee.id,
            date(2021, 6, 4),
            date(2021, 6, 8),
        )


def test_create_usage_rejects_insufficient_balance(
    vacation_session: Session,
) -> None:
    employee, _ = create_employee(vacation_session)
    create_allowance(vacation_session, employee.id, 2021, 3)

    with pytest.raises(InsufficientBalanceError):
        VacationService(vacation_session).create_usage(
            employee.id,
            date(2021, 6, 1),
            date(2021, 6, 5),
        )


def test_create_usage_rejects_missing_allowance(vacation_session: Session) -> None:
    employee, _ = create_employee(vacation_session)

    with pytest.raises(MissingAllowanceError):
        VacationService(vacation_session).create_usage(
            employee.id,
            date(2021, 6, 1),
            date(2021, 6, 2),
        )


def test_create_usage_rejects_cross_year_without_all_allowances(
    vacation_session: Session,
) -> None:
    employee, _ = create_employee(vacation_session)
    create_allowance(vacation_session, employee.id, 2020, 20)
    # No 2021 allowance

    with pytest.raises(MissingAllowanceError, match="2021"):
        VacationService(vacation_session).create_usage(
            employee.id,
            date(2020, 12, 30),
            date(2021, 1, 2),
        )
