"""
Tests for Research Notes API (Slice 3).

These tests run against a real PostgreSQL database (Docker-based, same as the app).
Alembic migrations must have been applied before running: make migrate && make test.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.research_note import AuditLog, NoteEntityLink, ResearchNote

# ── helpers ───────────────────────────────────────────────────────────────────


async def _cleanup_notes(db: AsyncSession) -> None:
    await db.execute(delete(NoteEntityLink))
    await db.execute(delete(AuditLog))
    await db.execute(delete(ResearchNote))
    await db.commit()


# ── create note ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_analyst_can_create_note(
    api_client: AsyncClient,
    analyst_token: str,
    db: AsyncSession,
) -> None:
    resp = await api_client.post(
        "/api/v1/notes",
        json={
            "title": "Test Note",
            "body_markdown": "# Hello\n\nWorld",
            "tags": ["gpu"],
        },
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["title"] == "Test Note"
    assert data["status"] == "draft"
    assert data["tags"] == ["gpu"]
    assert data["slug"] is None

    await _cleanup_notes(db)


@pytest.mark.asyncio
async def test_viewer_cannot_create_note(
    api_client: AsyncClient,
    viewer_token: str,
    db: AsyncSession,
) -> None:
    resp = await api_client.post(
        "/api/v1/notes",
        json={"title": "Blocked Note", "body_markdown": "Should fail"},
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert resp.status_code == 403

    await _cleanup_notes(db)


# ── list notes ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_notes_status_filter(
    api_client: AsyncClient,
    analyst_token: str,
    db: AsyncSession,
) -> None:
    # Create a draft and a review note
    for i, status_str in enumerate(["draft", "review"]):
        resp = await api_client.post(
            "/api/v1/notes",
            json={"title": f"Note {i}", "body_markdown": "body"},
            headers={"Authorization": f"Bearer {analyst_token}"},
        )
        assert resp.status_code == 201
        note_id = resp.json()["id"]
        if status_str == "review":
            await api_client.patch(
                f"/api/v1/notes/{note_id}",
                json={"status": "review"},
                headers={"Authorization": f"Bearer {analyst_token}"},
            )

    resp = await api_client.get(
        "/api/v1/notes?status=draft",
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert all(n["status"] == "draft" for n in data["items"])

    await _cleanup_notes(db)


@pytest.mark.asyncio
async def test_list_notes_tag_filter(
    api_client: AsyncClient,
    analyst_token: str,
    db: AsyncSession,
) -> None:
    await api_client.post(
        "/api/v1/notes",
        json={
            "title": "GPU Note",
            "body_markdown": "body",
            "tags": ["gpu", "datacenter"],
        },
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    await api_client.post(
        "/api/v1/notes",
        json={
            "title": "Supply Chain Note",
            "body_markdown": "body",
            "tags": ["supply-chain"],
        },
        headers={"Authorization": f"Bearer {analyst_token}"},
    )

    resp = await api_client.get(
        "/api/v1/notes?tag=gpu",
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) >= 1
    assert all("gpu" in n["tags"] for n in data["items"])

    await _cleanup_notes(db)


@pytest.mark.asyncio
async def test_viewer_only_sees_published(
    api_client: AsyncClient,
    analyst_token: str,
    viewer_token: str,
    db: AsyncSession,
) -> None:
    # Create a draft note
    resp = await api_client.post(
        "/api/v1/notes",
        json={"title": "Secret Draft", "body_markdown": "body"},
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert resp.status_code == 201

    # Viewer listing should see nothing (no published notes)
    resp = await api_client.get(
        "/api/v1/notes",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert all(n["status"] == "published" for n in data["items"])

    await _cleanup_notes(db)


# ── publish ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_publish_creates_slug_and_public_endpoint_works(
    api_client: AsyncClient,
    analyst_token: str,
    db: AsyncSession,
) -> None:
    create_resp = await api_client.post(
        "/api/v1/notes",
        json={"title": "H100 Deep Dive", "body_markdown": "## Analysis\n\nGreat GPU."},
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert create_resp.status_code == 201
    note_id = create_resp.json()["id"]

    pub_resp = await api_client.post(
        f"/api/v1/notes/{note_id}/publish",
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert pub_resp.status_code == 200, pub_resp.text
    data = pub_resp.json()
    assert data["status"] == "published"
    assert data["slug"] is not None
    assert data["published_at"] is not None
    slug = data["slug"]

    # Public endpoint — no auth
    public_resp = await api_client.get(f"/api/v1/published/{slug}")
    assert public_resp.status_code == 200
    assert public_resp.json()["title"] == "H100 Deep Dive"

    await _cleanup_notes(db)


@pytest.mark.asyncio
async def test_published_404_for_unknown_slug(
    api_client: AsyncClient,
) -> None:
    resp = await api_client.get("/api/v1/published/does-not-exist-abc12345")
    assert resp.status_code == 404


# ── RBAC edit ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_analyst_cannot_edit_another_analysts_note(
    api_client: AsyncClient,
    analyst_token: str,
    admin_token: str,
    db: AsyncSession,
) -> None:
    # Admin creates a note
    create_resp = await api_client.post(
        "/api/v1/notes",
        json={"title": "Admin Note", "body_markdown": "body"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert create_resp.status_code == 201
    note_id = create_resp.json()["id"]

    # Analyst tries to edit it
    edit_resp = await api_client.patch(
        f"/api/v1/notes/{note_id}",
        json={"title": "Hacked"},
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert edit_resp.status_code == 403

    await _cleanup_notes(db)


@pytest.mark.asyncio
async def test_admin_can_edit_any_note(
    api_client: AsyncClient,
    analyst_token: str,
    admin_token: str,
    db: AsyncSession,
) -> None:
    # Analyst creates a note
    create_resp = await api_client.post(
        "/api/v1/notes",
        json={"title": "Analyst Note", "body_markdown": "body"},
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert create_resp.status_code == 201
    note_id = create_resp.json()["id"]

    # Admin edits it
    edit_resp = await api_client.patch(
        f"/api/v1/notes/{note_id}",
        json={"title": "Admin Edited"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert edit_resp.status_code == 200
    assert edit_resp.json()["title"] == "Admin Edited"

    await _cleanup_notes(db)


# ── audit log ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_audit_log_populated_on_create(
    api_client: AsyncClient,
    admin_token: str,
    db: AsyncSession,
) -> None:
    resp = await api_client.post(
        "/api/v1/notes",
        json={"title": "Audit Test", "body_markdown": "body"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 201

    audit_resp = await api_client.get(
        "/api/v1/audit",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert audit_resp.status_code == 200
    actions = [e["action"] for e in audit_resp.json()["items"]]
    assert "note.created" in actions

    await _cleanup_notes(db)
