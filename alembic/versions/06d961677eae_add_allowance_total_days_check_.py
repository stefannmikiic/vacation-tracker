"""add allowance total days check constraint

Revision ID: 06d961677eae
Revises: 0001_initial
Create Date: 2026-07-29 20:16:12.758403

"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '06d961677eae'
down_revision: str | Sequence[str] | None = '0001_initial'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_allowance_total_days_nonneg",
        "vacation_allowances",
        "total_days >= 0",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_allowance_total_days_nonneg",
        "vacation_allowances",
        type_="check",
    )