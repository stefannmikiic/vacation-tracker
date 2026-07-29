"""Admin query endpoints for employees, allowances, and usages."""

import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from vacation_tracker.api.deps import AdminUser, DbSession
from vacation_tracker.core.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from vacation_tracker.repositories import (
    AllowanceRepository,
    EmployeeRepository,
    UsageRepository,
)
from vacation_tracker.schemas.admin import AllowanceResponse, EmployeeResponse
from vacation_tracker.schemas.usage import UsageResponse

router = APIRouter(prefix="/admin", tags=["admin-queries"])

LimitQuery = Annotated[int, Query(ge=1)]
OffsetQuery = Annotated[int, Query(ge=0)]
FromQuery = Annotated[date | None, Query(alias="from")]
ToQuery = Annotated[date | None, Query(alias="to")]


def _clamp_limit(limit: int) -> int:
    return max(1, min(limit, MAX_PAGE_SIZE))


def _resolve_usage_window(
    *,
    year: int | None,
    date_from: date | None,
    date_to: date | None,
) -> tuple[date, date] | None:
    """Build an inclusive date window from optional year / from / to filters.

    Returns:
        None when no date filters are set.
        A (start, end) pair when filters apply.
        Raises HTTP 400 for invalid from/to pairs.
        Returns a reversed pair (end < start) when year and from/to do not
        intersect — callers should treat that as an empty result.
    """
    if (date_from is None) ^ (date_to is None):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query params 'from' and 'to' must be provided together",
        )
    if date_from is not None and date_to is not None and date_to < date_from:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="'to' must be on or after 'from'",
        )

    window_start: date | None = date(year, 1, 1) if year is not None else None
    window_end: date | None = date(year, 12, 31) if year is not None else None

    if date_from is not None and date_to is not None:
        if window_start is None or window_end is None:
            return date_from, date_to
        return max(window_start, date_from), min(window_end, date_to)

    if window_start is not None and window_end is not None:
        return window_start, window_end

    return None


@router.get("/employees", response_model=list[EmployeeResponse])
def list_employees(
    db: DbSession,
    _admin: AdminUser,
    limit: LimitQuery = DEFAULT_PAGE_SIZE,
    offset: OffsetQuery = 0,
) -> list[EmployeeResponse]:
    employees = EmployeeRepository(db).list(
        limit=_clamp_limit(limit),
        offset=offset,
    )
    return [EmployeeResponse.model_validate(employee) for employee in employees]


@router.get(
    "/employees/{employee_id}/allowances",
    response_model=list[AllowanceResponse],
)
def list_employee_allowances(
    employee_id: uuid.UUID,
    db: DbSession,
    _admin: AdminUser,
) -> list[AllowanceResponse]:
    if EmployeeRepository(db).get_by_id(employee_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found",
        )

    allowances = AllowanceRepository(db).list_for_employee(employee_id)
    return [AllowanceResponse.model_validate(item) for item in allowances]


@router.get("/vacation-usages", response_model=list[UsageResponse])
def list_vacation_usages(
    db: DbSession,
    _admin: AdminUser,
    employee_id: uuid.UUID | None = None,
    year: int | None = None,
    date_from: FromQuery = None,
    date_to: ToQuery = None,
    limit: LimitQuery = DEFAULT_PAGE_SIZE,
    offset: OffsetQuery = 0,
) -> list[UsageResponse]:
    window = _resolve_usage_window(
        year=year,
        date_from=date_from,
        date_to=date_to,
    )
    if window is not None and window[1] < window[0]:
        return []

    window_start = window[0] if window else None
    window_end = window[1] if window else None

    usages = UsageRepository(db).list_filtered(
        employee_id=employee_id,
        window_start=window_start,
        window_end=window_end,
        limit=_clamp_limit(limit),
        offset=offset,
    )
    return [UsageResponse.model_validate(usage) for usage in usages]
