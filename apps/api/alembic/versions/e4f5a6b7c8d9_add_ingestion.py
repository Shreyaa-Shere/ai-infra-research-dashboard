"""add source_documents, source_entity_links, ingestion_runs

Revision ID: e4f5a6b7c8d9
Revises: d3e4f5a6b7c8
Create Date: 2026-03-04 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "e4f5a6b7c8d9"
down_revision: Union[str, None] = "d3e4f5a6b7c8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── New enums ─────────────────────────────────────────────────────────────
    op.execute("CREATE TYPE source_type AS ENUM ('rss', 'json', 'file')")
    op.execute(
        "CREATE TYPE ingestion_status AS ENUM ('ingested', 'skipped', 'error')"
    )
    op.execute(
        "CREATE TYPE run_status AS ENUM ('running', 'success', 'partial', 'error')"
    )

    # ── source_documents ──────────────────────────────────────────────────────
    op.create_table(
        "source_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("url", sa.String(2048), nullable=True),
        sa.Column("publisher", sa.String(256), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("extracted_entities", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "source_type",
            postgresql.ENUM("rss", "json", "file", name="source_type", create_type=False),
            nullable=False,
        ),
        sa.Column("source_name", sa.String(128), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "ingested", "skipped", "error",
                name="ingestion_status",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("content_hash"),
    )
    op.create_index(
        "ix_source_documents_content_hash", "source_documents", ["content_hash"], unique=True
    )
    op.create_index(
        "ix_source_documents_created_at", "source_documents", ["created_at"]
    )
    op.create_index(
        "ix_source_documents_published_at", "source_documents", ["published_at"]
    )
    op.create_index(
        "ix_source_documents_source",
        "source_documents",
        ["source_type", "source_name"],
    )

    # ── source_entity_links ───────────────────────────────────────────────────
    op.create_table(
        "source_entity_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_document_id", postgresql.UUID(as_uuid=True), nullable=False),
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
        sa.Column("entity_name", sa.String(256), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["source_document_id"], ["source_documents.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_document_id", "entity_type", "entity_id",
            name="uq_source_entity_link",
        ),
    )
    op.create_index(
        "ix_source_entity_links_doc_id",
        "source_entity_links",
        ["source_document_id"],
    )
    op.create_index(
        "ix_source_entity_links_entity",
        "source_entity_links",
        ["entity_type", "entity_id"],
    )

    # ── ingestion_runs ────────────────────────────────────────────────────────
    op.create_table(
        "ingestion_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("triggered_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "source_type",
            postgresql.ENUM("rss", "json", "file", name="source_type", create_type=False),
            nullable=False,
        ),
        sa.Column("source_name", sa.String(128), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "running", "success", "partial", "error",
                name="run_status",
                create_type=False,
            ),
            nullable=False,
            server_default="running",
        ),
        sa.Column("dry_run", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("stats", postgresql.JSONB(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["triggered_by"], ["users.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ingestion_runs_started_at", "ingestion_runs", ["started_at"]
    )
    op.create_index(
        "ix_ingestion_runs_status", "ingestion_runs", ["status"]
    )


def downgrade() -> None:
    op.drop_index("ix_ingestion_runs_status", table_name="ingestion_runs")
    op.drop_index("ix_ingestion_runs_started_at", table_name="ingestion_runs")
    op.drop_table("ingestion_runs")

    op.drop_index("ix_source_entity_links_entity", table_name="source_entity_links")
    op.drop_index("ix_source_entity_links_doc_id", table_name="source_entity_links")
    op.drop_table("source_entity_links")

    op.drop_index("ix_source_documents_source", table_name="source_documents")
    op.drop_index("ix_source_documents_published_at", table_name="source_documents")
    op.drop_index("ix_source_documents_created_at", table_name="source_documents")
    op.drop_index("ix_source_documents_content_hash", table_name="source_documents")
    op.drop_table("source_documents")

    op.execute("DROP TYPE run_status")
    op.execute("DROP TYPE ingestion_status")
    op.execute("DROP TYPE source_type")
