"""Initial QuantumRoute schema.

Revision ID: 20261117_0001
Revises:
Create Date: 2026-11-17
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20261117_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("full_name", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=True, server_default="user"),
        sa.Column("is_active", sa.Boolean(), nullable=True, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_username", "users", ["username"], unique=True)

    op.create_table(
        "optimization_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(), nullable=False), sa.Column("destination", sa.String(), nullable=False),
        sa.Column("vehicle_type", sa.String(), nullable=False), sa.Column("traffic_density", sa.String(), nullable=False),
        sa.Column("weather", sa.String(), nullable=False), sa.Column("road_condition", sa.String(), nullable=False),
        sa.Column("optimization_priority", sa.String(), nullable=False),
        sa.Column("quantum_result", sa.JSON(), nullable=True), sa.Column("dijkstra_result", sa.JSON(), nullable=True),
        sa.Column("astar_result", sa.JSON(), nullable=True), sa.Column("bellman_ford_result", sa.JSON(), nullable=True),
        sa.Column("traffic_prediction", sa.JSON(), nullable=True), sa.Column("nodes", sa.JSON(), nullable=True),
        sa.Column("edges", sa.JSON(), nullable=True), sa.Column("optimization_score", sa.Float(), nullable=True, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]), sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_optimization_records_id", "optimization_records", ["id"])


def downgrade() -> None:
    op.drop_index("ix_optimization_records_id", table_name="optimization_records")
    op.drop_table("optimization_records")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_id", table_name="users")
    op.drop_table("users")
