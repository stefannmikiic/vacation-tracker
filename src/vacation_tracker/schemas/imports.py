"""Pydantic schemas for admin import endpoints."""

from pydantic import BaseModel, ConfigDict


class ImportRowErrorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    row_number: int
    message: str


class ImportSummaryResponse(BaseModel):
    """Partial-success import result returned by admin import endpoints."""

    model_config = ConfigDict(from_attributes=True)

    created: int
    updated: int
    failed: int
    errors: list[ImportRowErrorResponse]
