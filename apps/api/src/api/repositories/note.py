from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.models.research_note import (
    AuditLog,
    EntityType,
    NoteEntityLink,
    NoteStatus,
    ResearchNote,
)
from api.models.user import Role


class NoteRepository:
    # ── helpers ──────────────────────────────────────────────────────────────

    def _with_rels(self):  # type: ignore[return]
        return selectinload(ResearchNote.author), selectinload(
            ResearchNote.entity_links
        )

    # ── list ─────────────────────────────────────────────────────────────────

    async def list(
        self,
        session: AsyncSession,
        limit: int,
        offset: int,
        *,
        current_user_id: uuid.UUID,
        current_user_role: Role,
        status: NoteStatus | None = None,
        tag: str | None = None,
        q: str | None = None,
    ) -> tuple[list[ResearchNote], int]:
        query = select(ResearchNote).options(*self._with_rels())
        count_q = select(func.count()).select_from(ResearchNote)

        # RBAC visibility filter
        if current_user_role == Role.viewer:
            query = query.where(ResearchNote.status == NoteStatus.published)
            count_q = count_q.where(ResearchNote.status == NoteStatus.published)
        elif current_user_role == Role.analyst:
            from sqlalchemy import or_

            vis = or_(
                ResearchNote.author_id == current_user_id,
                ResearchNote.status == NoteStatus.published,
            )
            query = query.where(vis)
            count_q = count_q.where(vis)
        # admin sees all — no extra filter

        if status:
            query = query.where(ResearchNote.status == status)
            count_q = count_q.where(ResearchNote.status == status)
        if tag:
            query = query.where(ResearchNote.tags.contains([tag]))
            count_q = count_q.where(ResearchNote.tags.contains([tag]))
        if q:
            from sqlalchemy import or_

            ilike = f"%{q}%"
            search = or_(
                ResearchNote.title.ilike(ilike),
                ResearchNote.body_markdown.ilike(ilike),
            )
            query = query.where(search)
            count_q = count_q.where(search)

        total = (await session.execute(count_q)).scalar_one()
        rows = await session.execute(
            query.order_by(ResearchNote.updated_at.desc()).limit(limit).offset(offset)
        )
        return list(rows.scalars().all()), total

    # ── get ───────────────────────────────────────────────────────────────────

    async def get(
        self, session: AsyncSession, note_id: uuid.UUID
    ) -> ResearchNote | None:
        result = await session.execute(
            select(ResearchNote)
            .options(*self._with_rels())
            .where(ResearchNote.id == note_id)
        )
        return result.scalar_one_or_none()

    async def get_by_slug(
        self, session: AsyncSession, slug: str
    ) -> ResearchNote | None:
        result = await session.execute(
            select(ResearchNote)
            .options(*self._with_rels())
            .where(ResearchNote.slug == slug)
        )
        return result.scalar_one_or_none()

    # ── create ────────────────────────────────────────────────────────────────

    async def create(
        self,
        session: AsyncSession,
        author_id: uuid.UUID,
        title: str,
        body_markdown: str,
        tags: list[str],
    ) -> ResearchNote:
        note = ResearchNote(
            id=uuid.uuid4(),
            author_id=author_id,
            title=title,
            body_markdown=body_markdown,
            tags=tags,
            status=NoteStatus.draft,
        )
        session.add(note)
        await session.flush()
        await session.refresh(note)
        return note

    # ── update ────────────────────────────────────────────────────────────────

    async def update(
        self,
        session: AsyncSession,
        note: ResearchNote,
        fields: dict,
    ) -> ResearchNote:
        for k, v in fields.items():
            setattr(note, k, v)
        await session.flush()
        await session.refresh(note)
        return note

    # ── delete ────────────────────────────────────────────────────────────────

    async def delete(self, session: AsyncSession, note: ResearchNote) -> None:
        await session.delete(note)
        await session.flush()

    # ── entity links ─────────────────────────────────────────────────────────

    async def replace_links(
        self,
        session: AsyncSession,
        note: ResearchNote,
        links: Sequence[tuple[EntityType, uuid.UUID]],
    ) -> None:
        """Atomically replace all entity links for a note."""
        from sqlalchemy import delete

        await session.execute(
            delete(NoteEntityLink).where(NoteEntityLink.note_id == note.id)
        )
        for entity_type, entity_id in links:
            session.add(
                NoteEntityLink(
                    id=uuid.uuid4(),
                    note_id=note.id,
                    entity_type=entity_type,
                    entity_id=entity_id,
                )
            )
        await session.flush()


class AuditLogRepository:
    async def append(
        self,
        session: AsyncSession,
        actor_user_id: uuid.UUID | None,
        action: str,
        entity_type: str,
        entity_id: str | None = None,
        meta_json: str | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            id=uuid.uuid4(),
            actor_user_id=actor_user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            meta_json=meta_json,
        )
        session.add(entry)
        await session.flush()
        return entry

    async def list(
        self, session: AsyncSession, limit: int = 20, offset: int = 0
    ) -> tuple[list[AuditLog], int]:
        from sqlalchemy import desc

        count = (
            await session.execute(select(func.count()).select_from(AuditLog))
        ).scalar_one()
        rows = await session.execute(
            select(AuditLog)
            .order_by(desc(AuditLog.created_at))
            .limit(limit)
            .offset(offset)
        )
        return list(rows.scalars().all()), count
