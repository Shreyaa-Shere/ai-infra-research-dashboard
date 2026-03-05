"""
Tests for Ingestion Pipeline (Slice 5).

Covers:
- IngestionService._compute_hash idempotency
- EntityExtractor.extract
- SourceDocument creation via service
- GET /api/v1/sources (list + filter)
- GET /api/v1/sources/{id} (detail)
- POST /api/v1/ingestion/run (trigger, RBAC)
- GET /api/v1/ingestion/runs (list)
"""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.source_document import IngestionRun, IngestionStatus, RunStatus, SourceDocument, SourceType
from api.models.user import User
from api.services.ingestion import IngestionService


# ── Helpers ───────────────────────────────────────────────────────────────────


async def _cleanup(db: AsyncSession) -> None:
    await db.execute(delete(IngestionRun))
    await db.execute(delete(SourceDocument))
    await db.commit()
    from api.services.cache import cache_delete_pattern
    try:
        await cache_delete_pattern("sources:*")
        await cache_delete_pattern("ingestion:runs:*")
    except Exception:
        pass


def _make_doc(suffix: str = "") -> dict:
    return {
        "title": f"Test Article {suffix}",
        "url": f"https://example.com/article-{suffix}",
        "source_name": "test-source",
        "published_at": "2024-01-15T10:00:00Z",
        "raw_text": f"NVIDIA H100 GPU deployed at Microsoft Azure datacenter. {suffix}",
    }


# ── Unit: content hash ────────────────────────────────────────────────────────


def test_compute_hash_deterministic() -> None:
    svc = IngestionService()
    item = _make_doc("a")
    h1 = svc._compute_hash(item)
    h2 = svc._compute_hash(item)
    assert h1 == h2
    assert len(h1) == 64  # sha256 hex


def test_compute_hash_differs_for_different_items() -> None:
    svc = IngestionService()
    h1 = svc._compute_hash(_make_doc("a"))
    h2 = svc._compute_hash(_make_doc("b"))
    assert h1 != h2


# ── Unit: entity extractor ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_extractor_returns_matched_entities(db: AsyncSession) -> None:
    from api.models.hardware_product import HardwareCategory, HardwareProduct
    from api.services.extractor import EntityExtractor

    # Ensure H100 exists in DB
    from sqlalchemy import select
    existing = (
        await db.execute(
            select(HardwareProduct).where(HardwareProduct.name == "H100")
        )
    ).scalar_one_or_none()
    if not existing:
        hw = HardwareProduct(
            id=uuid.uuid4(),
            name="H100",
            vendor="NVIDIA",
            category=HardwareCategory.GPU,
        )
        db.add(hw)
        await db.commit()

    extractor = EntityExtractor()
    result = await extractor.extract(
        db,
        title="NVIDIA H100 Training Cluster",
        raw_text="The H100 GPU from NVIDIA is widely used.",
    )

    assert isinstance(result, dict)
    assert "hardware_products" in result
    names = [e["name"] for e in result["hardware_products"]]
    assert "H100" in names


# ── Integration: sources list ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_sources_empty(
    api_client: AsyncClient,
    viewer_token: str,
    db: AsyncSession,
) -> None:
    await _cleanup(db)
    resp = await api_client.get(
        "/api/v1/sources",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert "total" in body


@pytest.mark.asyncio
async def test_list_sources_requires_auth(api_client: AsyncClient) -> None:
    resp = await api_client.get("/api/v1/sources")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_list_sources_with_inserted_doc(
    api_client: AsyncClient,
    viewer_token: str,
    db: AsyncSession,
) -> None:
    await _cleanup(db)

    doc = SourceDocument(
        id=uuid.uuid4(),
        content_hash="a" * 64,
        title="Test Source Document",
        url="https://example.com/test",
        source_name="test-feed",
        source_type=SourceType.file,
        raw_text="Some raw text content.",
        status=IngestionStatus.ingested,
    )
    db.add(doc)
    await db.commit()

    try:
        resp = await api_client.get(
            "/api/v1/sources",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 1
        titles = [item["title"] for item in body["items"]]
        assert "Test Source Document" in titles
    finally:
        await _cleanup(db)


@pytest.mark.asyncio
async def test_list_sources_filter_by_type(
    api_client: AsyncClient,
    viewer_token: str,
    db: AsyncSession,
) -> None:
    await _cleanup(db)

    file_doc = SourceDocument(
        id=uuid.uuid4(),
        content_hash="b" * 64,
        title="File Source",
        source_name="file-src",
        source_type=SourceType.file,
        status=IngestionStatus.ingested,
    )
    rss_doc = SourceDocument(
        id=uuid.uuid4(),
        content_hash="c" * 64,
        title="RSS Source",
        source_name="rss-src",
        source_type=SourceType.rss,
        status=IngestionStatus.ingested,
    )
    db.add_all([file_doc, rss_doc])
    await db.commit()

    try:
        resp = await api_client.get(
            "/api/v1/sources?source_type=file",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert all(item["source_type"] == "file" for item in body["items"])
    finally:
        await _cleanup(db)


# ── Integration: source detail ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_source_detail(
    api_client: AsyncClient,
    viewer_token: str,
    db: AsyncSession,
) -> None:
    await _cleanup(db)

    doc = SourceDocument(
        id=uuid.uuid4(),
        content_hash="d" * 64,
        title="Detail Test",
        url="https://example.com/detail",
        source_name="detail-src",
        source_type=SourceType.file,
        raw_text="Detail text.",
        status=IngestionStatus.ingested,
    )
    db.add(doc)
    await db.commit()

    try:
        resp = await api_client.get(
            f"/api/v1/sources/{doc.id}",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == str(doc.id)
        assert body["title"] == "Detail Test"
        assert "entity_links" in body
    finally:
        await _cleanup(db)


@pytest.mark.asyncio
async def test_get_source_not_found(
    api_client: AsyncClient,
    viewer_token: str,
) -> None:
    resp = await api_client.get(
        f"/api/v1/sources/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert resp.status_code == 404


# ── Integration: ingestion run trigger ────────────────────────────────────────


@pytest.mark.asyncio
async def test_viewer_cannot_trigger_run(
    api_client: AsyncClient,
    viewer_token: str,
) -> None:
    resp = await api_client.post(
        "/api/v1/ingestion/run",
        json={"source_type": "file", "source_name": "local-ingest"},
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_analyst_can_trigger_run(
    api_client: AsyncClient,
    analyst_token: str,
    db: AsyncSession,
) -> None:
    await _cleanup(db)

    # Patch out the Celery task so tests don't need a real broker
    mock_task = MagicMock()
    mock_task.delay.return_value = MagicMock(id="mock-task-id")
    with patch("api.workers.tasks.run_ingestion_task", mock_task):
        resp = await api_client.post(
            "/api/v1/ingestion/run",
            json={"source_type": "file", "source_name": "local-ingest", "dry_run": True},
            headers={"Authorization": f"Bearer {analyst_token}"},
        )

    assert resp.status_code == 202
    body = resp.json()
    assert "run_id" in body
    assert body["status"] == "running"
    assert "message" in body

    await _cleanup(db)


# ── Integration: ingestion runs list ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_runs_requires_analyst(
    api_client: AsyncClient,
    viewer_token: str,
) -> None:
    resp = await api_client.get(
        "/api/v1/ingestion/runs",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_list_runs_analyst_can_read(
    api_client: AsyncClient,
    analyst_token: str,
    db: AsyncSession,
) -> None:
    resp = await api_client.get(
        "/api/v1/ingestion/runs",
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body


# ── Unit: idempotency dedup ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_duplicate_hash_is_skipped(db: AsyncSession) -> None:
    await _cleanup(db)

    svc = IngestionService()
    item = _make_doc("dup")
    content_hash = svc._compute_hash(item)

    existing = SourceDocument(
        id=uuid.uuid4(),
        content_hash=content_hash,
        title=item["title"],
        source_name=item["source_name"],
        source_type=SourceType.file,
        status=IngestionStatus.ingested,
    )
    db.add(existing)
    await db.commit()

    try:
        from api.repositories.ingestion import IngestionRepository
        repo = IngestionRepository()
        found = await repo.get_by_hash(db, content_hash)
        assert found is not None
        assert found.id == existing.id
    finally:
        await _cleanup(db)
