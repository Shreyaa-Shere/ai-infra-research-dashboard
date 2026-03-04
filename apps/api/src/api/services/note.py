from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from api.models.research_note import EntityType, NoteStatus, ResearchNote
from api.models.user import Role, User
from api.repositories.note import AuditLogRepository, NoteRepository
from api.schemas.errors import api_error
from api.schemas.note import (
    AuthorInfo,
    LinkedEntityDisplay,
    LinkedEntityInput,
    ResearchNoteCreate,
    ResearchNoteResponse,
    ResearchNoteUpdate,
)
from api.schemas.pagination import PaginatedResponse
from api.services.cache import cache_delete_pattern, cache_get, cache_set

_repo = NoteRepository()
_audit = AuditLogRepository()

_LIST_PREFIX = "note:list"
_DETAIL_PREFIX = "note:detail"
_PUB_PREFIX = "note:pub"

_LIST_TTL = 60
_DETAIL_TTL = 60
_PUB_TTL = 300


# ── slug generation ───────────────────────────────────────────────────────────

def _make_slug(title: str, uid: uuid.UUID) -> str:
    slug = title.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_-]+", "-", slug)
    slug = slug.strip("-")
    short = str(uid).replace("-", "")[:8]
    return f"{slug}-{short}"


# ── entity display resolution ─────────────────────────────────────────────────

async def _resolve_entity_display(
    session: AsyncSession, entity_type: EntityType, entity_id: uuid.UUID
) -> dict[str, str] | None:
    if entity_type == EntityType.hardware_product:
        from api.models.hardware_product import HardwareProduct
        from sqlalchemy import select

        row = (
            await session.execute(
                select(HardwareProduct).where(HardwareProduct.id == entity_id)
            )
        ).scalar_one_or_none()
        if row:
            return {"name": row.name, "kind": row.category.value}
    elif entity_type == EntityType.company:
        from api.models.company import Company
        from sqlalchemy import select

        row = (
            await session.execute(select(Company).where(Company.id == entity_id))
        ).scalar_one_or_none()
        if row:
            return {"name": row.name, "kind": row.type.value}
    elif entity_type == EntityType.datacenter:
        from api.models.datacenter_site import DatacenterSite
        from sqlalchemy import select

        row = (
            await session.execute(
                select(DatacenterSite).where(DatacenterSite.id == entity_id)
            )
        ).scalar_one_or_none()
        if row:
            return {"name": row.name, "kind": row.status.value}
    return None


async def _validate_entity(
    session: AsyncSession, entity_type: EntityType, entity_id: uuid.UUID
) -> None:
    display = await _resolve_entity_display(session, entity_type, entity_id)
    if display is None:
        raise api_error(
            "ENTITY_NOT_FOUND",
            f"{entity_type.value} with id {entity_id} not found",
            404,
        )


# ── response builder ─────────────────────────────────────────────────────────

async def _build_response(
    session: AsyncSession, note: ResearchNote
) -> ResearchNoteResponse:
    linked: list[LinkedEntityDisplay] = []
    for link in note.entity_links:
        display = await _resolve_entity_display(
            session, link.entity_type, link.entity_id
        )
        linked.append(
            LinkedEntityDisplay(
                entity_type=link.entity_type,
                entity_id=link.entity_id,
                display=display if display else {"name": str(link.entity_id), "kind": "unknown"},
            )
        )

    return ResearchNoteResponse(
        id=note.id,
        title=note.title,
        body_markdown=note.body_markdown,
        status=note.status,
        slug=note.slug,
        tags=note.tags or [],
        author=AuthorInfo(id=note.author.id, email=note.author.email),
        linked_entities=linked,
        created_at=note.created_at,
        updated_at=note.updated_at,
        published_at=note.published_at,
    )


# ── cache helpers ─────────────────────────────────────────────────────────────

def _list_key(role: str, limit: int, offset: int, status: str, tag: str, q: str) -> str:
    return f"{_LIST_PREFIX}:{role}:{limit}:{offset}:{status}:{tag}:{q}"


def _detail_key(note_id: uuid.UUID) -> str:
    return f"{_DETAIL_PREFIX}:{note_id}"


def _pub_key(slug: str) -> str:
    return f"{_PUB_PREFIX}:{slug}"


async def _bust_caches(note_id: uuid.UUID, slug: str | None = None) -> None:
    await cache_delete_pattern(f"{_LIST_PREFIX}:*")
    await cache_delete_pattern(f"{_DETAIL_PREFIX}:{note_id}")
    if slug:
        await cache_delete_pattern(f"{_PUB_PREFIX}:{slug}")


# ── service ───────────────────────────────────────────────────────────────────

class NoteService:
    # ── list ──────────────────────────────────────────────────────────────────

    async def list_notes(
        self,
        session: AsyncSession,
        current_user: User,
        limit: int = 20,
        offset: int = 0,
        status: NoteStatus | None = None,
        tag: str | None = None,
        q: str | None = None,
    ) -> PaginatedResponse[ResearchNoteResponse]:
        cache_key = _list_key(
            current_user.role.value,
            limit,
            offset,
            status.value if status else "",
            tag or "",
            q or "",
        )
        cached = await cache_get(cache_key)
        if cached:
            return PaginatedResponse[ResearchNoteResponse].model_validate_json(cached)

        notes, total = await _repo.list(
            session,
            limit,
            offset,
            current_user_id=current_user.id,
            current_user_role=current_user.role,
            status=status,
            tag=tag,
            q=q,
        )
        items = [await _build_response(session, n) for n in notes]
        response = PaginatedResponse[ResearchNoteResponse](
            items=items, total=total, limit=limit, offset=offset
        )
        await cache_set(cache_key, response.model_dump_json(), _LIST_TTL)
        return response

    # ── get ───────────────────────────────────────────────────────────────────

    async def get_note(
        self, session: AsyncSession, note_id: uuid.UUID, current_user: User
    ) -> ResearchNoteResponse:
        cache_key = _detail_key(note_id)
        cached = await cache_get(cache_key)
        if cached:
            data = ResearchNoteResponse.model_validate_json(cached)
            _check_visibility(data.status, data.author.id, current_user)
            return data

        note = await _repo.get(session, note_id)
        if not note:
            raise api_error("NOT_FOUND", "Note not found", 404)
        _check_visibility(note.status, note.author_id, current_user)

        resp = await _build_response(session, note)
        await cache_set(cache_key, resp.model_dump_json(), _DETAIL_TTL)
        return resp

    # ── create ────────────────────────────────────────────────────────────────

    async def create_note(
        self,
        session: AsyncSession,
        data: ResearchNoteCreate,
        current_user: User,
    ) -> ResearchNoteResponse:
        if current_user.role == Role.viewer:
            raise api_error("FORBIDDEN", "Viewers cannot create notes", 403)

        # Validate entities
        for le in data.linked_entities:
            await _validate_entity(session, le.entity_type, le.entity_id)

        note = await _repo.create(
            session,
            author_id=current_user.id,
            title=data.title,
            body_markdown=data.body_markdown,
            tags=data.tags,
        )

        if data.linked_entities:
            await _repo.replace_links(
                session,
                note,
                [(le.entity_type, le.entity_id) for le in data.linked_entities],
            )

        await session.commit()

        note = await _repo.get(session, note.id)
        assert note is not None

        await _audit.append(
            session,
            actor_user_id=current_user.id,
            action="note.created",
            entity_type="research_note",
            entity_id=str(note.id),
            meta_json=json.dumps({"title": note.title}),
        )
        await session.commit()

        await _bust_caches(note.id)
        return await _build_response(session, note)

    # ── update ────────────────────────────────────────────────────────────────

    async def update_note(
        self,
        session: AsyncSession,
        note_id: uuid.UUID,
        data: ResearchNoteUpdate,
        current_user: User,
    ) -> ResearchNoteResponse:
        note = await _repo.get(session, note_id)
        if not note:
            raise api_error("NOT_FOUND", "Note not found", 404)

        _check_can_edit(note, current_user)

        # Prevent using update to publish (publish endpoint only)
        if data.status == NoteStatus.published:
            raise api_error(
                "INVALID_STATUS",
                "Use POST /notes/{id}/publish to publish a note",
                400,
            )

        # Prevent going backward in status (published → draft/review)
        if data.status and note.status == NoteStatus.published:
            raise api_error(
                "INVALID_STATUS",
                "Cannot change status of a published note via update",
                400,
            )

        fields: dict = {}
        if data.title is not None:
            fields["title"] = data.title
        if data.body_markdown is not None:
            fields["body_markdown"] = data.body_markdown
        if data.tags is not None:
            fields["tags"] = data.tags
        if data.status is not None:
            fields["status"] = data.status

        if fields:
            await _repo.update(session, note, fields)

        if data.linked_entities is not None:
            for le in data.linked_entities:
                await _validate_entity(session, le.entity_type, le.entity_id)
            await _repo.replace_links(
                session,
                note,
                [(le.entity_type, le.entity_id) for le in data.linked_entities],
            )

        await session.commit()

        note = await _repo.get(session, note_id)
        assert note is not None

        await _audit.append(
            session,
            actor_user_id=current_user.id,
            action="note.updated",
            entity_type="research_note",
            entity_id=str(note.id),
            meta_json=json.dumps({"fields": list(fields.keys())}),
        )
        await session.commit()

        await _bust_caches(note.id, note.slug)
        return await _build_response(session, note)

    # ── delete ────────────────────────────────────────────────────────────────

    async def delete_note(
        self,
        session: AsyncSession,
        note_id: uuid.UUID,
        current_user: User,
    ) -> None:
        note = await _repo.get(session, note_id)
        if not note:
            raise api_error("NOT_FOUND", "Note not found", 404)
        _check_can_edit(note, current_user)

        slug = note.slug
        await _repo.delete(session, note)

        await _audit.append(
            session,
            actor_user_id=current_user.id,
            action="note.deleted",
            entity_type="research_note",
            entity_id=str(note_id),
        )
        await session.commit()
        await _bust_caches(note_id, slug)

    # ── publish ───────────────────────────────────────────────────────────────

    async def publish_note(
        self,
        session: AsyncSession,
        note_id: uuid.UUID,
        current_user: User,
    ) -> ResearchNoteResponse:
        if current_user.role == Role.viewer:
            raise api_error("FORBIDDEN", "Viewers cannot publish notes", 403)

        note = await _repo.get(session, note_id)
        if not note:
            raise api_error("NOT_FOUND", "Note not found", 404)

        if current_user.role == Role.analyst and note.author_id != current_user.id:
            raise api_error("FORBIDDEN", "You can only publish your own notes", 403)

        if note.status == NoteStatus.published:
            raise api_error("CONFLICT", "Note is already published", 409)

        slug = note.slug or _make_slug(note.title, note.id)
        now = datetime.now(tz=timezone.utc)

        await _repo.update(
            session,
            note,
            {
                "status": NoteStatus.published,
                "slug": slug,
                "published_at": now,
            },
        )
        await session.commit()

        note = await _repo.get(session, note_id)
        assert note is not None

        await _audit.append(
            session,
            actor_user_id=current_user.id,
            action="note.published",
            entity_type="research_note",
            entity_id=str(note.id),
            meta_json=json.dumps({"slug": slug}),
        )
        await session.commit()

        await _bust_caches(note.id, slug)
        return await _build_response(session, note)

    # ── published (public) ───────────────────────────────────────────────────

    async def get_published(
        self, session: AsyncSession, slug: str
    ) -> ResearchNoteResponse:
        cache_key = _pub_key(slug)
        cached = await cache_get(cache_key)
        if cached:
            return ResearchNoteResponse.model_validate_json(cached)

        note = await _repo.get_by_slug(session, slug)
        if not note or note.status != NoteStatus.published:
            raise api_error("NOT_FOUND", "Published note not found", 404)

        resp = await _build_response(session, note)
        await cache_set(cache_key, resp.model_dump_json(), _PUB_TTL)
        return resp

    # ── entity links replace ─────────────────────────────────────────────────

    async def get_links(
        self, session: AsyncSession, note_id: uuid.UUID, current_user: User
    ) -> list[LinkedEntityDisplay]:
        note = await _repo.get(session, note_id)
        if not note:
            raise api_error("NOT_FOUND", "Note not found", 404)
        _check_visibility(note.status, note.author_id, current_user)
        resp = await _build_response(session, note)
        return resp.linked_entities

    async def replace_links(
        self,
        session: AsyncSession,
        note_id: uuid.UUID,
        links: list[LinkedEntityInput],
        current_user: User,
    ) -> list[LinkedEntityDisplay]:
        note = await _repo.get(session, note_id)
        if not note:
            raise api_error("NOT_FOUND", "Note not found", 404)
        _check_can_edit(note, current_user)

        for le in links:
            await _validate_entity(session, le.entity_type, le.entity_id)

        await _repo.replace_links(
            session, note, [(le.entity_type, le.entity_id) for le in links]
        )
        await session.commit()
        await _bust_caches(note.id, note.slug)

        note = await _repo.get(session, note_id)
        assert note is not None
        resp = await _build_response(session, note)
        return resp.linked_entities


# ── RBAC helpers ──────────────────────────────────────────────────────────────

def _check_visibility(
    status: NoteStatus, author_id: uuid.UUID, user: User
) -> None:
    if user.role == Role.admin:
        return
    if status == NoteStatus.published:
        return
    if user.role == Role.analyst and author_id == user.id:
        return
    raise api_error("FORBIDDEN", "You do not have access to this note", 403)


def _check_can_edit(note: ResearchNote, user: User) -> None:
    if user.role == Role.admin:
        return
    if user.role == Role.analyst and note.author_id == user.id:
        return
    raise api_error("FORBIDDEN", "You cannot edit this note", 403)
