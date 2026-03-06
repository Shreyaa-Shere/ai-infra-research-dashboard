"""Datacenter endpoint tests."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.company import Company
from api.models.datacenter_site import DatacenterSite

_BASE = "/api/v1/datacenters"


def _sample(suffix: str = "") -> dict:
    return {
        "name": f"Test DC {uuid.uuid4().hex[:6]}{suffix}",
        "region": "us-east-1",
        "status": "active",
        "power_mw": 120,
    }


async def _cleanup(db: AsyncSession, dc_id: str | None = None) -> None:
    if dc_id:
        await db.execute(
            delete(DatacenterSite).where(DatacenterSite.id == uuid.UUID(dc_id))
        )
    else:
        await db.execute(delete(DatacenterSite))
    await db.commit()


# ── list ──────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_datacenters_requires_auth(api_client: AsyncClient) -> None:
    resp = await api_client.get(_BASE)
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_list_datacenters_viewer(
    api_client: AsyncClient, viewer_token: str
) -> None:
    resp = await api_client.get(
        _BASE, headers={"Authorization": f"Bearer {viewer_token}"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert "total" in body


# ── create ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_datacenter_analyst(
    api_client: AsyncClient, analyst_token: str, db: AsyncSession
) -> None:
    data = _sample()
    resp = await api_client.post(
        _BASE, json=data, headers={"Authorization": f"Bearer {analyst_token}"}
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == data["name"]
    assert body["region"] == data["region"]
    assert body["status"] == "active"
    assert body["power_mw"] == 120
    await _cleanup(db, body["id"])


@pytest.mark.asyncio
async def test_create_datacenter_viewer_forbidden(
    api_client: AsyncClient, viewer_token: str
) -> None:
    resp = await api_client.post(
        _BASE, json=_sample(), headers={"Authorization": f"Bearer {viewer_token}"}
    )
    assert resp.status_code == 403


# ── get ───────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_datacenter(
    api_client: AsyncClient, admin_token: str, db: AsyncSession
) -> None:
    data = _sample()
    create = await api_client.post(
        _BASE, json=data, headers={"Authorization": f"Bearer {admin_token}"}
    )
    dc_id = create.json()["id"]

    resp = await api_client.get(
        f"{_BASE}/{dc_id}", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code == 200
    assert resp.json()["id"] == dc_id
    await _cleanup(db, dc_id)


@pytest.mark.asyncio
async def test_get_datacenter_not_found(
    api_client: AsyncClient, viewer_token: str
) -> None:
    resp = await api_client.get(
        f"{_BASE}/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert resp.status_code == 404


# ── update ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_datacenter(
    api_client: AsyncClient, admin_token: str, db: AsyncSession
) -> None:
    create = await api_client.post(
        _BASE, json=_sample(), headers={"Authorization": f"Bearer {admin_token}"}
    )
    dc_id = create.json()["id"]

    resp = await api_client.patch(
        f"{_BASE}/{dc_id}",
        json={"status": "retired", "power_mw": 200},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "retired"
    assert resp.json()["power_mw"] == 200
    await _cleanup(db, dc_id)


@pytest.mark.asyncio
async def test_update_datacenter_viewer_forbidden(
    api_client: AsyncClient, admin_token: str, viewer_token: str, db: AsyncSession
) -> None:
    create = await api_client.post(
        _BASE, json=_sample(), headers={"Authorization": f"Bearer {admin_token}"}
    )
    dc_id = create.json()["id"]

    resp = await api_client.patch(
        f"{_BASE}/{dc_id}",
        json={"status": "retired"},
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert resp.status_code == 403
    await _cleanup(db, dc_id)


# ── delete ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_delete_datacenter_admin(
    api_client: AsyncClient, admin_token: str, db: AsyncSession
) -> None:
    create = await api_client.post(
        _BASE, json=_sample(), headers={"Authorization": f"Bearer {admin_token}"}
    )
    dc_id = create.json()["id"]

    resp = await api_client.delete(
        f"{_BASE}/{dc_id}", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code == 204

    get_resp = await api_client.get(
        f"{_BASE}/{dc_id}", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_datacenter_analyst_forbidden(
    api_client: AsyncClient, admin_token: str, analyst_token: str, db: AsyncSession
) -> None:
    create = await api_client.post(
        _BASE, json=_sample(), headers={"Authorization": f"Bearer {admin_token}"}
    )
    dc_id = create.json()["id"]

    resp = await api_client.delete(
        f"{_BASE}/{dc_id}", headers={"Authorization": f"Bearer {analyst_token}"}
    )
    assert resp.status_code == 403
    await _cleanup(db, dc_id)


# ── filters ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_filter_by_status(
    api_client: AsyncClient, admin_token: str, db: AsyncSession
) -> None:
    active = {**_sample(), "status": "active"}
    planned = {**_sample(), "status": "planned"}

    r1 = await api_client.post(
        _BASE, json=active, headers={"Authorization": f"Bearer {admin_token}"}
    )
    r2 = await api_client.post(
        _BASE, json=planned, headers={"Authorization": f"Bearer {admin_token}"}
    )

    resp = await api_client.get(
        f"{_BASE}?status=active",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    statuses = [dc["status"] for dc in resp.json()["items"]]
    assert all(s == "active" for s in statuses)

    await _cleanup(db, r1.json()["id"])
    await _cleanup(db, r2.json()["id"])


@pytest.mark.asyncio
async def test_filter_by_owner_company(
    api_client: AsyncClient, admin_token: str, db: AsyncSession
) -> None:
    co = await api_client.post(
        "/api/v1/companies",
        json={
            "name": f"OwnerCo {uuid.uuid4().hex[:6]}",
            "type": "cloud",
            "region": "US",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    company_id = co.json()["id"]

    dc_data = {**_sample(), "owner_company_id": company_id}
    dc = await api_client.post(
        _BASE, json=dc_data, headers={"Authorization": f"Bearer {admin_token}"}
    )
    dc_id = dc.json()["id"]

    resp = await api_client.get(
        f"{_BASE}?owner_company_id={company_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    ids = [d["id"] for d in resp.json()["items"]]
    assert dc_id in ids

    await _cleanup(db, dc_id)
    await db.execute(delete(Company).where(Company.id == uuid.UUID(company_id)))
    await db.commit()
