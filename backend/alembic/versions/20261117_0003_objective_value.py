"""Store the normalized optimization objective explicitly.

Revision ID: 20261117_0003
Revises: 20261117_0002
Create Date: 2026-11-17
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20261117_0003"
down_revision: Union[str, None] = "20261117_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("optimization_records", sa.Column("objective_value", sa.Float(), nullable=True))
    op.execute(
        "UPDATE optimization_records SET objective_value = "
        "NULLIF(quantum_result->>'quantum_cost', '')::double precision "
        "WHERE quantum_result IS NOT NULL AND quantum_result->>'quantum_cost' IS NOT NULL"
    )


def downgrade() -> None:
    op.drop_column("optimization_records", "objective_value")
