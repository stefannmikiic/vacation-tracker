"""Employee ORM model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from vacation_tracker.core.constants import UserRole
from vacation_tracker.db.base import Base
from vacation_tracker.db.mixins import IDMixin, TimestampMixin

if TYPE_CHECKING:
    from vacation_tracker.db.models.allowance import VacationAllowance
    from vacation_tracker.db.models.usage import VacationUsage


class Employee(IDMixin, TimestampMixin, Base):
    __tablename__ = "employees"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(32), default=UserRole.EMPLOYEE.value)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    allowances: Mapped[list[VacationAllowance]] = relationship(
        back_populates="employee",
        cascade="all, delete-orphan",
    )
    usages: Mapped[list[VacationUsage]] = relationship(
        back_populates="employee",
        cascade="all, delete-orphan",
    )
