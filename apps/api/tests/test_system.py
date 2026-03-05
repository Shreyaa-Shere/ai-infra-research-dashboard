"""
Tests for:
  - /api/v1/system/info (admin only)
  - Global error handlers (consistent format + request_id)
  - X-Request-Id response header presence
"""

import pytest
from httpx import AsyncClient

# ── /api/v1/system/info ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_system_info_requires_auth(api_client: AsyncClient) -> None:
    resp = await api_client.get("/api/v1/system/info")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_system_info_forbidden_for_analyst(
    api_client: AsyncClient, analyst_token: str
) -> None:
    resp = await api_client.get(
        "/api/v1/system/info",
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert resp.status_code == 403
    body = resp.json()
    assert body["error"]["code"] == "forbidden"


@pytest.mark.asyncio
async def test_system_info_admin(api_client: AsyncClient, admin_token: str) -> None:
    resp = await api_client.get(
        "/api/v1/system/info",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "version" in body
    assert "uptime_seconds" in body
    assert isinstance(body["db_connected"], bool)
    assert isinstance(body["redis_connected"], bool)
    assert "environment" in body


# ── X-Request-Id header ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_request_id_in_response_header(api_client: AsyncClient) -> None:
    resp = await api_client.get("/healthz")
    assert "x-request-id" in resp.headers
    assert len(resp.headers["x-request-id"]) > 0


@pytest.mark.asyncio
async def test_request_id_echoed_when_provided(api_client: AsyncClient) -> None:
    resp = await api_client.get(
        "/healthz", headers={"X-Request-Id": "my-custom-id-123"}
    )
    assert resp.headers.get("x-request-id") == "my-custom-id-123"


# ── Consistent error format ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_validation_error_format(api_client: AsyncClient) -> None:
    """POST /auth/login with invalid payload → standard error envelope."""
    resp = await api_client.post("/api/v1/auth/login", json={"email": "not-an-email"})
    assert resp.status_code == 422
    body = resp.json()
    assert "error" in body
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert "errors" in body["error"]["details"]
    assert "request_id" in body["error"]["details"]


@pytest.mark.asyncio
async def test_http_error_contains_request_id(api_client: AsyncClient) -> None:
    """401 from protected endpoint includes request_id in error details."""
    resp = await api_client.get("/api/v1/users")
    assert resp.status_code == 401
    body = resp.json()
    assert "error" in body
    assert "request_id" in body["error"].get("details", {})
