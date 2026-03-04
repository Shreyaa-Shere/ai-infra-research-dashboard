"""Company endpoint tests."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.company import Company

_BASE = "/api/v1/companies"


def _sample(suffix: str = "") -> dict:
    name = f"TestCo {uuid.uuid4().hex[:6]}{suffix}"
    return {"name": name, "type": "vendor", "region": "US", "website": "https://example.com"}


@pytest.mark.asyncio
async def test_list_companies(api_client: AsyncClient, viewer_token: str) -> None:
    resp = await api_client.get(_BASE, headers={"Authorization": f"Bearer {viewer_token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert "total" in body


@pytest.mark.asyncio
async def test_create_company(
    api_client: AsyncClient, admin_token: str, db: AsyncSession
) -> None:
    data = _sample()
    resp = await api_client.post(
        _BASE, json=data, headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == data["name"]
    await db.execute(delete(Company).where(Company.name == data["name"]))
    await db.commit()


@pytest.mark.asyncio
async def test_duplicate_company_name_rejected(
    api_client: AsyncClient, admin_token: str, db: AsyncSession
) -> None:
    data = _sample()
    await api_client.post(_BASE, json=data, headers={"Authorization": f"Bearer {admin_token}"})
    resp = await api_client.post(_BASE, json=data, headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 409
    await db.execute(delete(Company).where(Company.name == data["name"]))
    await db.commit()


@pytest.mark.asyncio
async def test_company_datacenter_relationship(
    api_client: AsyncClient, admin_token: str, db: AsyncSession
) -> None:
    co_data = _sample()
    co_resp = await api_client.post(
        _BASE, json=co_data, headers={"Authorization": f"Bearer {admin_token}"}
    )
    company_id = co_resp.json()["id"]

    dc_resp = await api_client.post(
        "/api/v1/datacenters",
        json={"name": "Test DC", "region": "us-east-1", "owner_company_id": company_id, "status": "active"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert dc_resp.status_code == 201
    assert dc_resp.json()["owner_company"]["id"] == company_id

    dc_id = dc_resp.json()["id"]
    await api_client.delete(f"/api/v1/datacenters/{dc_id}", headers={"Authorization": f"Bearer {admin_token}"})
    await db.execute(delete(Company).where(Company.name == co_data["name"]))
    await db.commit()
