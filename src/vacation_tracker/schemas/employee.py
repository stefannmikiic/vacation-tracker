"""Pydantic schemas for employee vacation endpoints."""

from datetime import date

from pydantic import BaseModel, ConfigDict, model_validator


class VacationSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    year: int
    total_days: int
    used_days: int
    available_days: int


class CreateUsageRequest(BaseModel):
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def validate_date_order(self) -> "CreateUsageRequest":
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self
