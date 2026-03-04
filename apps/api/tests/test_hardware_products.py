"""
Hardware product endpoint tests.
Requires: make dev && make migrate
"""

import datetime
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.hardware_product import HardwareCategory, HardwareProduct

_BASE = "/api/v1/hardware-products"

_SAMPLE = {
    "name": "Test GPU",
    "vendor": "TestVendor",
    "category": "GPU",
    "release_date": "2024-01-01",
    "memory_gb": 40,
    "tdp_watts": 300,
    "process_node": "7nm",
}


async def _cleanup_by_vendor(db: AsyncSession, vendor: str) -> None:
    await db.execute(delete(HardwareProduct).where(HardwareProduct.vendor == vendor))
    await db.commit()


@pytest.mark.asyncio
async def test_list_requires_auth(api_client: AsyncClient) -> None:
    resp = await api_client.get(_BASE)
    assert resp.status_code == 401  # FastAPI >=0.110 HTTPBearer returns 401 for missing token


@pytest.mark.asyncio
async def test_list_hardware_products(
    api_client: AsyncClient, viewer_token: str
) -> None:
    resp = await api_client.get(
        _BASE, headers={"Authorization": f"Bearer {viewer_token}"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert "total" in body
    assert "limit" in body
    assert "offset" in body


@pytest.mark.asyncio
async def test_create_hardware_product(
    api_client: AsyncClient, admin_token: str, db: AsyncSession
) -> None:
    resp = await api_client.post(
        _BASE,
        json=_SAMPLE,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == _SAMPLE["name"]
    assert body["vendor"] == _SAMPLE["vendor"]
    assert body["category"] == "GPU"
    assert "id" in body
    await _cleanup_by_vendor(db, _SAMPLE["vendor"])


@pytest.mark.asyncio
async def test_create_requires_analyst_or_admin(
    api_client: AsyncClient, viewer_token: str
) -> None:
    resp = await api_client.post(
        _BASE,
        json=_SAMPLE,
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_analyst_can_create(
    api_client: AsyncClient, analyst_token: str, db: AsyncSession
) -> None:
    resp = await api_client.post(
        _BASE,
        json=_SAMPLE,
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert resp.status_code == 201
    await _cleanup_by_vendor(db, _SAMPLE["vendor"])


@pytest.mark.asyncio
async def test_get_hardware_product(
    api_client: AsyncClient, admin_token: str, db: AsyncSession
) -> None:
    create_resp = await api_client.post(
        _BASE,
        json=_SAMPLE,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    item_id = create_resp.json()["id"]

    resp = await api_client.get(
        f"{_BASE}/{item_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["id"] == item_id
    await _cleanup_by_vendor(db, _SAMPLE["vendor"])


@pytest.mark.asyncio
async def test_update_hardware_product(
    api_client: AsyncClient, analyst_token: str, db: AsyncSession
) -> None:
    create_resp = await api_client.post(
        _BASE,
        json=_SAMPLE,
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    item_id = create_resp.json()["id"]

    resp = await api_client.patch(
        f"{_BASE}/{item_id}",
        json={"memory_gb": 80},
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["memory_gb"] == 80
    await _cleanup_by_vendor(db, _SAMPLE["vendor"])


@pytest.mark.asyncio
async def test_delete_requires_admin(
    api_client: AsyncClient,
    analyst_token: str,
    admin_token: str,
    db: AsyncSession,
) -> None:
    create_resp = await api_client.post(
        _BASE,
        json=_SAMPLE,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    item_id = create_resp.json()["id"]

    # Analyst cannot delete
    resp = await api_client.delete(
        f"{_BASE}/{item_id}",
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert resp.status_code == 403

    # Admin can delete
    resp = await api_client.delete(
        f"{_BASE}/{item_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_pagination(
    api_client: AsyncClient, admin_token: str, db: AsyncSession
) -> None:
    vendor = f"PaginationTestVendor_{uuid.uuid4().hex[:6]}"
    for i in range(3):
        await api_client.post(
            _BASE,
            json={**_SAMPLE, "name": f"GPU {i}", "vendor": vendor},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

    resp = await api_client.get(
        f"{_BASE}?limit=2&offset=0&vendor={vendor}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 3
    assert len(body["items"]) == 2
    assert body["limit"] == 2
    assert body["offset"] == 0

    await _cleanup_by_vendor(db, vendor)


@pytest.mark.asyncio
async def test_get_not_found(
    api_client: AsyncClient, viewer_token: str
) -> None:
    resp = await api_client.get(
        f"{_BASE}/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert resp.status_code == 404
