"""Shared vacation-usage response schema."""

import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict


class UsageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    employee_id: uuid.UUID
    start_date: date
    end_date: date
