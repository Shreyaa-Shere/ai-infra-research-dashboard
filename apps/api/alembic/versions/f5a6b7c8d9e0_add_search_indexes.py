"""Add GIN indexes for full-text search (unified search, Slice 6).

Revision ID: f5a6b7c8d9e0
Revises: e4f5a6b7c8d9
Create Date: 2026-03-04 00:00:00.000000

"""

from alembic import op

revision = "f5a6b7c8d9e0"
down_revision = "e4f5a6b7c8d9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # GIN index for FTS on research_notes (title + body_markdown)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_research_notes_fts "
        "ON research_notes USING GIN "
        "(to_tsvector('english', coalesce(title, '') || ' ' || coalesce(body_markdown, '')))"
    )
    # GIN index for FTS on source_documents (title + raw_text)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_source_documents_fts "
        "ON source_documents USING GIN "
        "(to_tsvector('english', coalesce(title, '') || ' ' || coalesce(raw_text, '')))"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_research_notes_fts")
    op.execute("DROP INDEX IF EXISTS ix_source_documents_fts")
