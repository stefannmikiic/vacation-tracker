"""Employee self-service vacation endpoints."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from vacation_tracker.api.deps import CurrentUser, DbSession
from vacation_tracker.core.exceptions import (
    InsufficientBalanceError,
    MissingAllowanceError,
    OverlappingUsageError,
)
from vacation_tracker.schemas.employee import (
    CreateUsageRequest,
    VacationSummaryResponse,
)
from vacation_tracker.schemas.usage import UsageResponse
from vacation_tracker.services.vacation_service import VacationService

router = APIRouter(prefix="/me/vacations", tags=["employee-vacations"])

FromQuery = Annotated[date, Query(alias="from")]
ToQuery = Annotated[date, Query(alias="to")]


@router.get("/summary", response_model=VacationSummaryResponse)
def get_my_vacation_summary(
    year: int,
    db: DbSession,
    current_user: CurrentUser,
) -> VacationSummaryResponse:
    summary = VacationService(db).get_summary(current_user.id, year)
    return VacationSummaryResponse.model_validate(summary)


@router.get("/usages", response_model=list[UsageResponse])
def list_my_vacation_usages(
    db: DbSession,
    current_user: CurrentUser,
    date_from: FromQuery,
    date_to: ToQuery,
) -> list[UsageResponse]:
    if date_to < date_from:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="'to' must be on or after 'from'",
        )

    try:
        usages = VacationService(db).list_usages(
            current_user.id,
            date_from,
            date_to,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return [UsageResponse.model_validate(usage) for usage in usages]


@router.post(
    "/usages",
    response_model=UsageResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_my_vacation_usage(
    body: CreateUsageRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> UsageResponse:
    service = VacationService(db)
    try:
        usage = service.create_usage(
            current_user.id,
            body.start_date,
            body.end_date,
        )
    except OverlappingUsageError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=exc.message,
        ) from exc
    except (InsufficientBalanceError, MissingAllowanceError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.message,
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return UsageResponse.model_validate(usage)
