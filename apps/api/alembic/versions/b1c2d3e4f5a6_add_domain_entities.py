"""add domain entities

Revision ID: b1c2d3e4f5a6
Revises: a3f8b2c4d1e5
Create Date: 2026-03-04 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "b1c2d3e4f5a6"
down_revision: Union[str, None] = "a3f8b2c4d1e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Enum types ────────────────────────────────────────────────────────────
    op.execute("CREATE TYPE hardware_category AS ENUM ('GPU', 'CPU', 'Networking', 'Accelerator')")
    op.execute("CREATE TYPE company_type AS ENUM ('fab', 'idm', 'cloud', 'vendor', 'research')")
    op.execute("CREATE TYPE datacenter_status AS ENUM ('planned', 'active', 'retired')")

    # ── companies ─────────────────────────────────────────────────────────────
    op.create_table(
        "companies",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "type",
            postgresql.ENUM(
                "fab", "idm", "cloud", "vendor", "research",
                name="company_type", create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("region", sa.String(128), nullable=False),
        sa.Column("website", sa.String(512), nullable=True),
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
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_companies_name", "companies", ["name"], unique=True)
    op.create_index("ix_companies_type", "companies", ["type"])

    # ── hardware_products ─────────────────────────────────────────────────────
    op.create_table(
        "hardware_products",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("vendor", sa.String(255), nullable=False),
        sa.Column(
            "category",
            postgresql.ENUM(
                "GPU", "CPU", "Networking", "Accelerator",
                name="hardware_category", create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("release_date", sa.Date(), nullable=True),
        sa.Column("memory_gb", sa.Integer(), nullable=True),
        sa.Column("tdp_watts", sa.Integer(), nullable=True),
        sa.Column("process_node", sa.String(64), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
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
    )
    op.create_index("ix_hardware_products_vendor", "hardware_products", ["vendor"])
    op.create_index("ix_hardware_products_category", "hardware_products", ["category"])

    # ── datacenter_sites ──────────────────────────────────────────────────────
    op.create_table(
        "datacenter_sites",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("region", sa.String(128), nullable=False),
        sa.Column("owner_company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("power_mw", sa.Integer(), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM(
                "planned", "active", "retired",
                name="datacenter_status", create_type=False,
            ),
            nullable=False,
            server_default="planned",
        ),
        sa.Column("notes", sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["owner_company_id"], ["companies.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_datacenter_sites_region", "datacenter_sites", ["region"])
    op.create_index("ix_datacenter_sites_status", "datacenter_sites", ["status"])
    op.create_index(
        "ix_datacenter_sites_owner_company_id",
        "datacenter_sites",
        ["owner_company_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_datacenter_sites_owner_company_id", table_name="datacenter_sites")
    op.drop_index("ix_datacenter_sites_status", table_name="datacenter_sites")
    op.drop_index("ix_datacenter_sites_region", table_name="datacenter_sites")
    op.drop_table("datacenter_sites")

    op.drop_index("ix_hardware_products_category", table_name="hardware_products")
    op.drop_index("ix_hardware_products_vendor", table_name="hardware_products")
    op.drop_table("hardware_products")

    op.drop_index("ix_companies_type", table_name="companies")
    op.drop_index("ix_companies_name", table_name="companies")
    op.drop_table("companies")

    op.execute("DROP TYPE datacenter_status")
    op.execute("DROP TYPE company_type")
    op.execute("DROP TYPE hardware_category")
