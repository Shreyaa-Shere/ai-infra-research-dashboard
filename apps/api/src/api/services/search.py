"""Unified search service — FTS across ResearchNotes + SourceDocuments."""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from api.models.user import Role, User
from api.repositories.search import search_notes, search_sources
from api.schemas.errors import api_error
from api.schemas.search import NoteSearchResult, SearchResponse, SourceSearchResult
from api.services.cache import cache_get, cache_set

_CACHE_PREFIX = "search"
_CACHE_TTL = 60


def _cache_key(
    q: str,
    type_: str,
    limit: int,
    offset: int,
    role: str,
    tags_str: str,
    status_filter: str,
    entity_type: str,
    entity_id: str,
    start: str,
    end: str,
    source_type: str,
) -> str:
    raw = "|".join(
        [
            q, type_, str(limit), str(offset), role,
            tags_str, status_filter, entity_type, entity_id,
            start, end, source_type,
        ]
    )
    return f"{_CACHE_PREFIX}:{hashlib.md5(raw.encode()).hexdigest()}"


def _enum_val(v: object) -> str:
    return v.value if hasattr(v, "value") else str(v)


def _truncate(text: str, max_len: int = 200) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len].rstrip() + "…"


class SearchService:
    async def search(
        self,
        session: AsyncSession,
        current_user: User,
        q: str,
        type_: str = "all",
        limit: int = 20,
        offset: int = 0,
        tags: list[str] | None = None,
        status_filter: str | None = None,
        entity_type: str | None = None,
        entity_id: uuid.UUID | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
        source_type: str | None = None,
    ) -> SearchResponse:
        q = q.strip()
        if not q:
            raise api_error("VALIDATION_ERROR", "Query must not be empty", 422)
        if len(q) > 300:
            raise api_error(
                "VALIDATION_ERROR", "Query must not exceed 300 characters", 422
            )

        ck = _cache_key(
            q, type_, limit, offset, current_user.role.value,
            ",".join(sorted(tags or [])),
            status_filter or "",
            entity_type or "",
            str(entity_id) if entity_id else "",
            start.isoformat() if start else "",
            end.isoformat() if end else "",
            source_type or "",
        )
        cached = await cache_get(ck)
        if cached:
            return SearchResponse.model_validate_json(cached)

        viewer_only = current_user.role == Role.viewer
        is_analyst = current_user.role == Role.analyst

        # For "all" type: fetch enough from each source to cover offset+limit
        sub_limit = (offset + limit) if type_ == "all" else limit
        sub_offset = 0 if type_ == "all" else offset

        note_items: list[NoteSearchResult] = []
        source_items: list[SourceSearchResult] = []
        note_total = 0
        source_total = 0

        if type_ in ("all", "note"):
            note_rows, note_total = await search_notes(
                session,
                q,
                sub_limit,
                sub_offset,
                viewer_only=viewer_only,
                current_user_id=current_user.id,
                is_analyst=is_analyst,
                tags=tags,
                status_filter=status_filter,
                entity_type=entity_type,
                entity_id=entity_id,
                start=start,
                end=end,
            )
            note_items = [
                NoteSearchResult(
                    id=r["id"],
                    title=r["title"],
                    snippet=r["snippet"] or _truncate(r.get("body_markdown") or "", 200),
                    score=float(r["rank"]),
                    status=_enum_val(r["status"]),
                    tags=list(r["tags"] or []),
                    author_id=r["author_id"],
                    slug=r["slug"],
                    published_at=r["published_at"],
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                )
                for r in note_rows
            ]

        if type_ in ("all", "source"):
            source_rows, source_total = await search_sources(
                session,
                q,
                sub_limit,
                sub_offset,
                source_type=source_type,
                entity_type=entity_type,
                entity_id=entity_id,
                start=start,
                end=end,
            )
            source_items = [
                SourceSearchResult(
                    id=r["id"],
                    title=r["title"],
                    snippet=r["snippet"] or _truncate(r.get("raw_text") or "", 200),
                    score=float(r["rank"]),
                    url=r.get("url"),
                    source_name=r["source_name"],
                    source_type=_enum_val(r["source_type"]),
                    status=_enum_val(r["status"]),
                    published_at=r.get("published_at"),
                    created_at=r["created_at"],
                )
                for r in source_rows
            ]

        if type_ == "all":
            merged = sorted(
                note_items + source_items, key=lambda x: x.score, reverse=True
            )
            total = note_total + source_total
            items: list[NoteSearchResult | SourceSearchResult] = merged[offset: offset + limit]
        elif type_ == "note":
            total = note_total
            items = note_items  # type: ignore[assignment]
        else:
            total = source_total
            items = source_items  # type: ignore[assignment]

        resp = SearchResponse(
            items=items, total=total, limit=limit, offset=offset, query=q
        )
        await cache_set(ck, resp.model_dump_json(), _CACHE_TTL)
        return resp
