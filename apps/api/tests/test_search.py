"""
Tests for Unified Search (Slice 6).

Covers:
- GET /api/v1/search requires auth (401)
- Empty query returns 422
- Query too long returns 422
- type=note returns only notes
- type=source returns only sources
- RBAC: viewer sees only published notes
- RBAC: analyst sees own + published notes
- Filter by source_type
- No results returns 200 with empty items
"""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.research_note import NoteStatus, ResearchNote
from api.models.source_document import IngestionStatus, SourceDocument, SourceType
from api.models.user import User

# ── Helpers ───────────────────────────────────────────────────────────────────


async def _cleanup_search_data(db: AsyncSession) -> None:
    await db.execute(delete(ResearchNote))
    await db.execute(delete(SourceDocument))
    await db.commit()
    from api.services.cache import cache_delete_pattern

    try:
        await cache_delete_pattern("search:*")
        await cache_delete_pattern("note:*")
        await cache_delete_pattern("sources:*")
    except Exception:
        pass


async def _insert_note(
    db: AsyncSession,
    author: User,
    title: str,
    body: str,
    status: NoteStatus = NoteStatus.published,
) -> ResearchNote:
    note = ResearchNote(
        id=uuid.uuid4(),
        title=title,
        body_markdown=body,
        status=status,
        author_id=author.id,
        tags=[],
    )
    db.add(note)
    await db.commit()
    return note


async def _insert_source(
    db: AsyncSession,
    title: str,
    raw_text: str,
    source_type: SourceType = SourceType.file,
) -> SourceDocument:
    doc = SourceDocument(
        id=uuid.uuid4(),
        content_hash=uuid.uuid4().hex * 2,  # 64-char unique hash
        title=title,
        source_name="test-feed",
        source_type=source_type,
        raw_text=raw_text,
        status=IngestionStatus.ingested,
    )
    db.add(doc)
    await db.commit()
    return doc


# ── Auth ──────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_search_requires_auth(api_client: AsyncClient) -> None:
    resp = await api_client.get("/api/v1/search?q=NVIDIA")
    assert resp.status_code == 401


# ── Validation ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_search_empty_query_rejected(
    api_client: AsyncClient,
    viewer_token: str,
) -> None:
    resp = await api_client.get(
        "/api/v1/search?q= ",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    # FastAPI rejects min_length=1 with 422 before reaching the service
    assert resp.status_code in (422, 400)


@pytest.mark.asyncio
async def test_search_query_too_long_rejected(
    api_client: AsyncClient,
    viewer_token: str,
) -> None:
    long_q = "x" * 301
    resp = await api_client.get(
        f"/api/v1/search?q={long_q}",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_search_invalid_type_rejected(
    api_client: AsyncClient,
    viewer_token: str,
) -> None:
    resp = await api_client.get(
        "/api/v1/search?q=test&type=invalid",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert resp.status_code == 422


# ── Basic search ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_search_returns_200_with_no_results(
    api_client: AsyncClient,
    viewer_token: str,
    db: AsyncSession,
) -> None:
    await _cleanup_search_data(db)
    resp = await api_client.get(
        "/api/v1/search?q=xyzzy_nonexistent_token_12345",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert "total" in body
    assert body["total"] == 0
    assert body["items"] == []


@pytest.mark.asyncio
async def test_search_finds_source_document(
    api_client: AsyncClient,
    viewer_token: str,
    db: AsyncSession,
) -> None:
    await _cleanup_search_data(db)
    await _insert_source(
        db,
        title="NVIDIA H100 GPU Deployment",
        raw_text="The H100 SXM5 GPU is deployed at scale in modern AI datacenters.",
    )
    try:
        resp = await api_client.get(
            "/api/v1/search?q=H100&type=source",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 1
        titles = [item["title"] for item in body["items"]]
        assert "NVIDIA H100 GPU Deployment" in titles
        # Result type discriminator
        assert body["items"][0]["type"] == "source"
    finally:
        await _cleanup_search_data(db)


@pytest.mark.asyncio
async def test_search_finds_research_note(
    api_client: AsyncClient,
    analyst_token: str,
    analyst_user: User,
    db: AsyncSession,
) -> None:
    await _cleanup_search_data(db)
    await _insert_note(
        db,
        author=analyst_user,
        title="AMD MI300X Datacenter Analysis",
        body="The MI300X accelerator is used in large-scale AI training clusters.",
        status=NoteStatus.published,
    )
    try:
        resp = await api_client.get(
            "/api/v1/search?q=MI300X&type=note",
            headers={"Authorization": f"Bearer {analyst_token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 1
        titles = [item["title"] for item in body["items"]]
        assert "AMD MI300X Datacenter Analysis" in titles
        assert body["items"][0]["type"] == "note"
    finally:
        await _cleanup_search_data(db)


# ── RBAC ──────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_viewer_only_sees_published_notes(
    api_client: AsyncClient,
    viewer_token: str,
    analyst_user: User,
    db: AsyncSession,
) -> None:
    await _cleanup_search_data(db)
    unique = "Xe2vQ9n"
    await _insert_note(
        db,
        analyst_user,
        f"{unique} Published Note",
        f"Content about {unique} chips.",
        NoteStatus.published,
    )
    await _insert_note(
        db,
        analyst_user,
        f"{unique} Draft Note",
        f"Draft content about {unique} GPUs.",
        NoteStatus.draft,
    )
    try:
        resp = await api_client.get(
            f"/api/v1/search?q={unique}&type=note",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        titles = [item["title"] for item in body["items"]]
        assert any("Published Note" in t for t in titles)
        assert not any("Draft Note" in t for t in titles)
    finally:
        await _cleanup_search_data(db)


@pytest.mark.asyncio
async def test_analyst_sees_own_draft_note(
    api_client: AsyncClient,
    analyst_token: str,
    analyst_user: User,
    db: AsyncSession,
) -> None:
    await _cleanup_search_data(db)
    unique = "Xy7wKm3"
    await _insert_note(
        db,
        analyst_user,
        f"{unique} Own Draft Note",
        f"Private draft about {unique} silicon.",
        NoteStatus.draft,
    )
    try:
        resp = await api_client.get(
            f"/api/v1/search?q={unique}&type=note",
            headers={"Authorization": f"Bearer {analyst_token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        titles = [item["title"] for item in body["items"]]
        assert any("Own Draft Note" in t for t in titles)
    finally:
        await _cleanup_search_data(db)


# ── Filters ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_filter_by_source_type(
    api_client: AsyncClient,
    viewer_token: str,
    db: AsyncSession,
) -> None:
    await _cleanup_search_data(db)
    unique = "Zp4xRn8"
    await _insert_source(
        db, f"{unique} File Article", f"About {unique} GPU clusters.", SourceType.file
    )
    await _insert_source(
        db,
        f"{unique} RSS Article",
        f"RSS feed about {unique} AI chips.",
        SourceType.rss,
    )
    try:
        resp = await api_client.get(
            f"/api/v1/search?q={unique}&type=source&source_type=file",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert all(item["source_type"] == "file" for item in body["items"])
    finally:
        await _cleanup_search_data(db)


@pytest.mark.asyncio
async def test_search_all_type_returns_both(
    api_client: AsyncClient,
    analyst_token: str,
    analyst_user: User,
    db: AsyncSession,
) -> None:
    await _cleanup_search_data(db)
    unique = "Wn5yTq2"
    await _insert_note(
        db,
        analyst_user,
        f"{unique} Research Note",
        f"Research on {unique} hardware.",
        NoteStatus.published,
    )
    await _insert_source(
        db, f"{unique} Source Doc", f"Industry data on {unique} chips."
    )
    try:
        resp = await api_client.get(
            f"/api/v1/search?q={unique}&type=all",
            headers={"Authorization": f"Bearer {analyst_token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        types = {item["type"] for item in body["items"]}
        assert "note" in types
        assert "source" in types
    finally:
        await _cleanup_search_data(db)


@pytest.mark.asyncio
async def test_search_response_shape(
    api_client: AsyncClient,
    viewer_token: str,
    db: AsyncSession,
) -> None:
    await _cleanup_search_data(db)
    await _insert_source(
        db,
        "Quantum GPU Architecture Overview",
        "This article covers quantum GPU architectures and next-gen AI chips.",
    )
    try:
        resp = await api_client.get(
            "/api/v1/search?q=GPU&type=source",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert "total" in body
        assert "limit" in body
        assert "offset" in body
        assert "query" in body
        if body["items"]:
            item = body["items"][0]
            assert "type" in item
            assert "title" in item
            assert "snippet" in item
            assert "score" in item
    finally:
        await _cleanup_search_data(db)
