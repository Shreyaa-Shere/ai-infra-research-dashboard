"""add metric_series and metric_points

Revision ID: d3e4f5a6b7c8
Revises: c2d3e4f5a6b7
Create Date: 2026-03-04 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "d3e4f5a6b7c8"
down_revision: Union[str, None] = "c2d3e4f5a6b7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── New enum for metric frequency ─────────────────────────────────────────
    op.execute(
        "CREATE TYPE metric_frequency AS ENUM ('daily', 'weekly', 'monthly')"
    )

    # ── metric_series ─────────────────────────────────────────────────────────
    op.create_table(
        "metric_series",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column(
            "entity_type",
            postgresql.ENUM(
                "hardware_product", "company", "datacenter",
                name="entity_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("unit", sa.String(64), nullable=False),
        sa.Column(
            "frequency",
            postgresql.ENUM(
                "daily", "weekly", "monthly",
                name="metric_frequency",
                create_type=False,
            ),
            nullable=False,
            server_default="monthly",
        ),
        sa.Column("source", sa.String(256), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "name", "entity_type", "entity_id", "unit", "frequency",
            name="uq_metric_series",
        ),
    )
    op.create_index("ix_metric_series_name", "metric_series", ["name"])
    op.create_index("ix_metric_series_entity_type", "metric_series", ["entity_type"])
    op.create_index("ix_metric_series_entity_id", "metric_series", ["entity_id"])

    # ── metric_points ─────────────────────────────────────────────────────────
    op.create_table(
        "metric_points",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("metric_series_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(
            ["metric_series_id"], ["metric_series.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "metric_series_id", "timestamp", name="uq_metric_point"
        ),
    )
    op.create_index(
        "ix_metric_points_series_id", "metric_points", ["metric_series_id"]
    )
    op.create_index("ix_metric_points_timestamp", "metric_points", ["timestamp"])


def downgrade() -> None:
    op.drop_index("ix_metric_points_timestamp", table_name="metric_points")
    op.drop_index("ix_metric_points_series_id", table_name="metric_points")
    op.drop_table("metric_points")

    op.drop_index("ix_metric_series_entity_id", table_name="metric_series")
    op.drop_index("ix_metric_series_entity_type", table_name="metric_series")
    op.drop_index("ix_metric_series_name", table_name="metric_series")
    op.drop_table("metric_series")

    op.execute("DROP TYPE metric_frequency")
