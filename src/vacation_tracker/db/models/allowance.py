"""Vacation allowance ORM model (total days per employee per year)."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from vacation_tracker.db.base import Base
from vacation_tracker.db.mixins import IDMixin, TimestampMixin

if TYPE_CHECKING:
    from vacation_tracker.db.models.employee import Employee


class VacationAllowance(IDMixin, TimestampMixin, Base):
    __tablename__ = "vacation_allowances"
    __table_args__ = (
        UniqueConstraint("employee_id", "year", name="uq_allowance_employee_year"),
        CheckConstraint(
            "total_days >= 0",
            name="ck_allowance_total_days_nonneg",
        ),
    )

    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("employees.id", ondelete="CASCADE"),
        index=True,
    )
    year: Mapped[int] = mapped_column(Integer)
    total_days: Mapped[int] = mapped_column(Integer)

    employee: Mapped[Employee] = relationship(back_populates="allowances")