"""
Tests for Metrics API (Slice 4).

Run against a real PostgreSQL DB inside Docker:
    make migrate && make test
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.metric import MetricEntityType, MetricFrequency, MetricPoint, MetricSeries


# ── helpers ───────────────────────────────────────────────────────────────────


async def _cleanup(db: AsyncSession) -> None:
    await db.execute(delete(MetricPoint))
    await db.execute(delete(MetricSeries))
    await db.commit()


async def _make_hw(db: AsyncSession) -> uuid.UUID:
    """Return the ID of an existing HardwareProduct (H100), or create a stub."""
    from sqlalchemy import select
    from api.models.hardware_product import HardwareProduct, HardwareCategory

    row = (
        await db.execute(select(HardwareProduct).where(HardwareProduct.name == "H100"))
    ).scalar_one_or_none()
    if row:
        return row.id

    hw = HardwareProduct(
        id=uuid.uuid4(),
        name=f"TestGPU-{uuid.uuid4().hex[:6]}",
        vendor="TestVendor",
        category=HardwareCategory.GPU,
    )
    db.add(hw)
    await db.commit()
    await db.refresh(hw)
    return hw.id


# ── create series ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_analyst_can_create_series(
    api_client: AsyncClient,
    analyst_token: str,
    db: AsyncSession,
) -> None:
    hw_id = await _make_hw(db)
    resp = await api_client.post(
        "/api/v1/metric-series",
        json={
            "name": "Test GPU Shipments",
            "entity_type": "hardware_product",
            "entity_id": str(hw_id),
            "unit": "units",
            "frequency": "monthly",
        },
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["name"] == "Test GPU Shipments"
    assert data["unit"] == "units"
    assert data["frequency"] == "monthly"
    await _cleanup(db)


@pytest.mark.asyncio
async def test_viewer_cannot_create_series(
    api_client: AsyncClient,
    viewer_token: str,
    db: AsyncSession,
) -> None:
    hw_id = await _make_hw(db)
    resp = await api_client.post(
        "/api/v1/metric-series",
        json={
            "name": "Blocked",
            "entity_type": "hardware_product",
            "entity_id": str(hw_id),
            "unit": "units",
        },
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert resp.status_code == 403
    await _cleanup(db)


# ── list series ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_series_returns_paginated(
    api_client: AsyncClient,
    admin_token: str,
    db: AsyncSession,
) -> None:
    hw_id = await _make_hw(db)
    # Create two series
    for name in ["Series A", "Series B"]:
        await api_client.post(
            "/api/v1/metric-series",
            json={
                "name": name,
                "entity_type": "hardware_product",
                "entity_id": str(hw_id),
                "unit": "units",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )

    resp = await api_client.get(
        "/api/v1/metric-series",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert data["total"] >= 2
    await _cleanup(db)


# ── bulk upsert idempotency ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_bulk_upsert_idempotent(
    api_client: AsyncClient,
    analyst_token: str,
    db: AsyncSession,
) -> None:
    hw_id = await _make_hw(db)
    # Create series
    create_resp = await api_client.post(
        "/api/v1/metric-series",
        json={
            "name": "Upsert Test Series",
            "entity_type": "hardware_product",
            "entity_id": str(hw_id),
            "unit": "units",
        },
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert create_resp.status_code == 201
    series_id = create_resp.json()["id"]

    points_payload = {
        "points": [
            {"timestamp": "2025-01-01T00:00:00Z", "value": 100.0},
            {"timestamp": "2025-02-01T00:00:00Z", "value": 120.0},
        ]
    }

    # First upsert
    r1 = await api_client.post(
        f"/api/v1/metric-series/{series_id}/points",
        json=points_payload,
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert r1.status_code == 200
    assert r1.json()["upserted"] == 2

    # Second upsert (same timestamps, different values) — should update
    points_payload["points"][0]["value"] = 999.0
    r2 = await api_client.post(
        f"/api/v1/metric-series/{series_id}/points",
        json=points_payload,
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert r2.status_code == 200
    assert r2.json()["upserted"] == 2

    # Verify point count is still 2 (not 4)
    r3 = await api_client.get(
        f"/api/v1/metric-series/{series_id}/points",
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert r3.status_code == 200
    pts = r3.json()
    assert len(pts) == 2
    # Updated value should be 999
    jan_pt = next(p for p in pts if "2025-01" in p["timestamp"])
    assert jan_pt["value"] == 999.0

    await _cleanup(db)


# ── date range filter ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_points_date_range(
    api_client: AsyncClient,
    analyst_token: str,
    db: AsyncSession,
) -> None:
    hw_id = await _make_hw(db)
    create_resp = await api_client.post(
        "/api/v1/metric-series",
        json={
            "name": "Date Range Test",
            "entity_type": "hardware_product",
            "entity_id": str(hw_id),
            "unit": "units",
        },
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    series_id = create_resp.json()["id"]

    await api_client.post(
        f"/api/v1/metric-series/{series_id}/points",
        json={
            "points": [
                {"timestamp": "2025-01-01T00:00:00Z", "value": 10},
                {"timestamp": "2025-06-01T00:00:00Z", "value": 20},
                {"timestamp": "2025-12-01T00:00:00Z", "value": 30},
            ]
        },
        headers={"Authorization": f"Bearer {analyst_token}"},
    )

    # Filter: only first half of 2025
    r = await api_client.get(
        f"/api/v1/metric-series/{series_id}/points"
        "?from_ts=2025-01-01T00:00:00Z&to_ts=2025-07-01T00:00:00Z",
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert r.status_code == 200
    pts = r.json()
    assert len(pts) == 2

    await _cleanup(db)


# ── overview shape ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_overview_shape(
    api_client: AsyncClient,
    admin_token: str,
    db: AsyncSession,
) -> None:
    resp = await api_client.get(
        "/api/v1/metrics/overview",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "kpis" in data
    assert "charts" in data
    assert isinstance(data["kpis"], list)
    assert isinstance(data["charts"], list)
    # KPIs include entity counts
    labels = [k["label"] for k in data["kpis"]]
    assert "Hardware Products" in labels
    assert "Companies" in labels


# ── CSV export ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_csv_export(
    api_client: AsyncClient,
    analyst_token: str,
    db: AsyncSession,
) -> None:
    hw_id = await _make_hw(db)
    create_resp = await api_client.post(
        "/api/v1/metric-series",
        json={
            "name": "CSV Export Test",
            "entity_type": "hardware_product",
            "entity_id": str(hw_id),
            "unit": "units",
        },
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    series_id = create_resp.json()["id"]

    await api_client.post(
        f"/api/v1/metric-series/{series_id}/points",
        json={"points": [{"timestamp": "2025-01-01T00:00:00Z", "value": 42.0}]},
        headers={"Authorization": f"Bearer {analyst_token}"},
    )

    r = await api_client.get(
        f"/api/v1/metric-series/{series_id}/export.csv",
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]
    body = r.text
    assert "timestamp" in body
    assert "42.0" in body

    await _cleanup(db)


# ── admin-only delete ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_only_admin_can_delete_series(
    api_client: AsyncClient,
    analyst_token: str,
    admin_token: str,
    db: AsyncSession,
) -> None:
    hw_id = await _make_hw(db)
    create_resp = await api_client.post(
        "/api/v1/metric-series",
        json={
            "name": "Delete Test",
            "entity_type": "hardware_product",
            "entity_id": str(hw_id),
            "unit": "units",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    series_id = create_resp.json()["id"]

    # Analyst cannot delete
    r_analyst = await api_client.delete(
        f"/api/v1/metric-series/{series_id}",
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert r_analyst.status_code == 403

    # Admin can delete
    r_admin = await api_client.delete(
        f"/api/v1/metric-series/{series_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r_admin.status_code == 204

    await _cleanup(db)
