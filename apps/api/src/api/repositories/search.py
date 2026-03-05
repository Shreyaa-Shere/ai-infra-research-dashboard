"""Search repository — PostgreSQL full-text search queries."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.research_note import NoteEntityLink, NoteStatus, ResearchNote
from api.models.source_document import SourceDocument, SourceEntityLink

_HEADLINE_OPTS = (
    "MaxWords=20,MinWords=5,StartSel=<mark>,StopSel=</mark>,HighlightAll=FALSE"
)


# ── Notes search ──────────────────────────────────────────────────────────────


async def search_notes(
    session: AsyncSession,
    q: str,
    limit: int,
    offset: int,
    *,
    viewer_only: bool = False,
    current_user_id: uuid.UUID | None = None,
    is_analyst: bool = False,
    tags: list[str] | None = None,
    status_filter: str | None = None,
    entity_type: str | None = None,
    entity_id: uuid.UUID | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
) -> tuple[list[dict], int]:
    q_expr = func.websearch_to_tsquery("english", q)
    fts_vec = func.to_tsvector(
        "english",
        func.coalesce(ResearchNote.title, "")
        + " "
        + func.coalesce(ResearchNote.body_markdown, ""),
    )
    rank_expr = func.ts_rank(fts_vec, q_expr).label("rank")
    headline_expr = func.ts_headline(
        "english",
        func.coalesce(ResearchNote.body_markdown, ResearchNote.title),
        q_expr,
        _HEADLINE_OPTS,
    ).label("snippet")

    filters = [fts_vec.op("@@")(q_expr)]

    # RBAC
    if viewer_only:
        filters.append(ResearchNote.status == NoteStatus.published)
    elif is_analyst and current_user_id:
        from sqlalchemy import or_

        filters.append(
            or_(
                ResearchNote.author_id == current_user_id,
                ResearchNote.status == NoteStatus.published,
            )
        )

    if status_filter:
        filters.append(ResearchNote.status == status_filter)

    if tags:
        for tag in tags:
            filters.append(ResearchNote.tags.contains([tag]))

    if entity_type and entity_id:
        sub = (
            select(NoteEntityLink.note_id)
            .where(
                NoteEntityLink.entity_type == entity_type,
                NoteEntityLink.entity_id == entity_id,
            )
            .scalar_subquery()
        )
        filters.append(ResearchNote.id.in_(sub))

    if start:
        filters.append(ResearchNote.created_at >= start)
    if end:
        filters.append(ResearchNote.created_at <= end)

    count_stmt = select(func.count()).select_from(ResearchNote).where(*filters)
    total = (await session.execute(count_stmt)).scalar_one()

    stmt = (
        select(
            ResearchNote.id,
            ResearchNote.title,
            ResearchNote.status,
            ResearchNote.tags,
            ResearchNote.author_id,
            ResearchNote.slug,
            ResearchNote.published_at,
            ResearchNote.created_at,
            ResearchNote.updated_at,
            rank_expr,
            headline_expr,
        )
        .where(*filters)
        .order_by(rank_expr.desc())
        .limit(limit)
        .offset(offset)
    )
    rows = (await session.execute(stmt)).mappings().all()
    return [dict(r) for r in rows], total


# ── Sources search ────────────────────────────────────────────────────────────


async def search_sources(
    session: AsyncSession,
    q: str,
    limit: int,
    offset: int,
    *,
    source_type: str | None = None,
    entity_type: str | None = None,
    entity_id: uuid.UUID | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
) -> tuple[list[dict], int]:
    q_expr = func.websearch_to_tsquery("english", q)
    fts_vec = func.to_tsvector(
        "english",
        func.coalesce(SourceDocument.title, "")
        + " "
        + func.coalesce(SourceDocument.raw_text, ""),
    )
    rank_expr = func.ts_rank(fts_vec, q_expr).label("rank")
    headline_expr = func.ts_headline(
        "english",
        func.coalesce(SourceDocument.raw_text, SourceDocument.title),
        q_expr,
        _HEADLINE_OPTS,
    ).label("snippet")

    filters = [fts_vec.op("@@")(q_expr)]

    if source_type:
        filters.append(SourceDocument.source_type == source_type)

    if entity_type and entity_id:
        sub = (
            select(SourceEntityLink.source_document_id)
            .where(
                SourceEntityLink.entity_type == entity_type,
                SourceEntityLink.entity_id == entity_id,
            )
            .scalar_subquery()
        )
        filters.append(SourceDocument.id.in_(sub))

    if start:
        filters.append(SourceDocument.created_at >= start)
    if end:
        filters.append(SourceDocument.created_at <= end)

    count_stmt = select(func.count()).select_from(SourceDocument).where(*filters)
    total = (await session.execute(count_stmt)).scalar_one()

    stmt = (
        select(
            SourceDocument.id,
            SourceDocument.title,
            SourceDocument.url,
            SourceDocument.source_name,
            SourceDocument.source_type,
            SourceDocument.status,
            SourceDocument.published_at,
            SourceDocument.created_at,
            rank_expr,
            headline_expr,
        )
        .where(*filters)
        .order_by(rank_expr.desc())
        .limit(limit)
        .offset(offset)
    )
    rows = (await session.execute(stmt)).mappings().all()
    return [dict(r) for r in rows], total
