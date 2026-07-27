"""Vacation usage ORM model (used leave date ranges)."""

from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from vacation_tracker.db.base import Base
from vacation_tracker.db.mixins import IDMixin, TimestampMixin

if TYPE_CHECKING:
    from vacation_tracker.db.models.employee import Employee


class VacationUsage(IDMixin, TimestampMixin, Base):
    __tablename__ = "vacation_usages"
    __table_args__ = (
        CheckConstraint(
            "start_date <= end_date",
            name="ck_usage_start_before_end",
        ),
    )

    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("employees.id", ondelete="CASCADE"),
        index=True,
    )
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)

    employee: Mapped[Employee] = relationship(back_populates="usages")
