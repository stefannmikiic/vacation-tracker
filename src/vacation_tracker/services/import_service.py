"""Import use-cases: parse → persist with partial success."""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from vacation_tracker.core.constants import UserRole
from vacation_tracker.core.logging import get_logger
from vacation_tracker.core.security import hash_password
from vacation_tracker.db.models import Employee, VacationUsage
from vacation_tracker.imports.pipeline import (
    parse_allowances,
    parse_employees,
    parse_usages,
)
from vacation_tracker.imports.rows import ImportRowError
from vacation_tracker.repositories import (
    AllowanceRepository,
    EmployeeRepository,
    UsageRepository,
)

logger = get_logger(__name__)


@dataclass
class ImportSummary:
    """Outcome of an import job (partial success allowed)."""

    created: int = 0
    updated: int = 0
    failed: int = 0
    errors: list[ImportRowError] = field(default_factory=list)


class ImportService:
    """Orchestrate import pipeline + repository persistence."""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._employees = EmployeeRepository(session)
        self._allowances = AllowanceRepository(session)
        self._usages = UsageRepository(session)

    def import_employees(self, content: bytes, filename: str) -> ImportSummary:
        """Parse employee profiles and create/update password hashes."""
        try:
            parsed = parse_employees(content, filename)
            summary = ImportSummary(errors=list(parsed.errors))

            for row in parsed.rows:
                existing = self._employees.get_by_email(row.email)
                password_hash = hash_password(row.password)
                if existing is None:
                    self._employees.add(
                        Employee(
                            email=row.email,
                            password_hash=password_hash,
                            role=UserRole.EMPLOYEE.value,
                        )
                    )
                    self._session.flush()
                    summary.created += 1
                else:
                    if existing.role == UserRole.ADMIN.value:
                        summary.errors.append(
                            ImportRowError(
                                row.row_number,
                                f"Cannot update admin via import: {row.email}",
                            )
                        )
                        continue

                    existing.password_hash = password_hash
                    summary.updated += 1

            summary.failed = len(summary.errors)
            self._session.commit()
            logger.info(
                "Employee import done: created=%s updated=%s failed=%s file=%s",
                summary.created,
                summary.updated,
                summary.failed,
                filename,
            )
            return summary
        except Exception:
            self._session.rollback()
            raise

    def import_allowances(self, content: bytes, filename: str) -> ImportSummary:
        """Parse allowances and upsert by employee + year."""
        try:
            parsed = parse_allowances(content, filename)
            summary = ImportSummary(errors=list(parsed.errors))

            for row in parsed.rows:
                employee = self._employees.get_by_email(row.email)
                if employee is None:
                    summary.errors.append(
                        ImportRowError(
                            row.row_number,
                            f"Unknown employee email: {row.email}",
                        )
                    )
                    continue

                existing = self._allowances.get_for_employee_year(
                    employee.id,
                    row.year,
                )
                self._allowances.upsert(employee.id, row.year, row.total_days)
                self._session.flush()
                if existing is None:
                    summary.created += 1
                else:
                    summary.updated += 1

            summary.failed = len(summary.errors)
            self._session.commit()
            logger.info(
                "Allowance import done: created=%s updated=%s failed=%s file=%s",
                summary.created,
                summary.updated,
                summary.failed,
                filename,
            )
            return summary
        except Exception:
            self._session.rollback()
            raise

    def import_usages(self, content: bytes, filename: str) -> ImportSummary:
        """Parse usages and create new records; reject overlaps/duplicates."""
        try:
            parsed = parse_usages(content, filename)
            summary = ImportSummary(errors=list(parsed.errors))

            for row in parsed.rows:
                employee = self._employees.get_by_email(row.email)
                if employee is None:
                    summary.errors.append(
                        ImportRowError(
                            row.row_number,
                            f"Unknown employee email: {row.email}",
                        )
                    )
                    continue

                overlapping = self._usages.find_overlapping(
                    employee.id,
                    row.start_date,
                    row.end_date,
                )
                if overlapping:
                    summary.errors.append(
                        ImportRowError(
                            row.row_number,
                            "Overlapping or duplicate vacation usage exists "
                            f"for {row.start_date}–{row.end_date}",
                        )
                    )
                    continue

                self._usages.add(
                    VacationUsage(
                        employee_id=employee.id,
                        start_date=row.start_date,
                        end_date=row.end_date,
                    )
                )
                # Make this row visible to later overlap checks in the same import.
                self._session.flush()
                summary.created += 1

            summary.failed = len(summary.errors)
            self._session.commit()
            logger.info(
                "Usage import done: created=%s updated=%s failed=%s file=%s",
                summary.created,
                summary.updated,
                summary.failed,
                filename,
            )
            return summary
        except Exception:
            self._session.rollback()
            raise
