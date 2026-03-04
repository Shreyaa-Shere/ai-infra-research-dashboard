"""add research notes, entity links, audit logs

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-03-04 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "c2d3e4f5a6b7"
down_revision: Union[str, None] = "b1c2d3e4f5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Enum types ─────────────────────────────────────────────────────────────
    op.execute(
        "CREATE TYPE note_status AS ENUM ('draft', 'review', 'published')"
    )
    op.execute(
        "CREATE TYPE entity_type AS ENUM ('hardware_product', 'company', 'datacenter')"
    )

    # ── research_notes ─────────────────────────────────────────────────────────
    op.create_table(
        "research_notes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("body_markdown", sa.Text(), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "draft", "review", "published",
                name="note_status",
                create_type=False,
            ),
            nullable=False,
            server_default="draft",
        ),
        sa.Column("slug", sa.String(600), nullable=True),
        sa.Column(
            "tags",
            postgresql.ARRAY(sa.String()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("author_id", postgresql.UUID(as_uuid=True), nullable=False),
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
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["author_id"], ["users.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_research_notes_status", "research_notes", ["status"])
    op.create_index("ix_research_notes_slug", "research_notes", ["slug"], unique=True)
    op.create_index("ix_research_notes_author_id", "research_notes", ["author_id"])

    # ── note_entity_links ──────────────────────────────────────────────────────
    op.create_table(
        "note_entity_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("note_id", postgresql.UUID(as_uuid=True), nullable=False),
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
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["note_id"], ["research_notes.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "note_id", "entity_type", "entity_id", name="uq_note_entity_link"
        ),
    )
    op.create_index(
        "ix_note_entity_links_note_id", "note_entity_links", ["note_id"]
    )

    # ── audit_logs ─────────────────────────────────────────────────────────────
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("entity_type", sa.String(64), nullable=False),
        sa.Column("entity_id", sa.String(255), nullable=True),
        sa.Column("meta_json", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["actor_user_id"], ["users.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_actor_user_id", "audit_logs", ["actor_user_id"])


def downgrade() -> None:
    op.drop_index("ix_audit_logs_actor_user_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_action", table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index("ix_note_entity_links_note_id", table_name="note_entity_links")
    op.drop_table("note_entity_links")

    op.drop_index("ix_research_notes_author_id", table_name="research_notes")
    op.drop_index("ix_research_notes_slug", table_name="research_notes")
    op.drop_index("ix_research_notes_status", table_name="research_notes")
    op.drop_table("research_notes")

    op.execute("DROP TYPE entity_type")
    op.execute("DROP TYPE note_status")
