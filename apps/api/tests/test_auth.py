"""
Auth endpoint tests.
Requires the stack to be running: make dev && make migrate
"""

import pytest
from httpx import AsyncClient

from api.models.user import User

PASSWORD = "Testpassword1!"


@pytest.mark.asyncio
async def test_login_success(api_client: AsyncClient, test_user: User) -> None:
    resp = await api_client.post(
        "/api/v1/auth/login",
        json={"email": test_user.email, "password": PASSWORD},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["user"]["email"] == test_user.email
    assert body["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(api_client: AsyncClient, test_user: User) -> None:
    resp = await api_client.post(
        "/api/v1/auth/login",
        json={"email": test_user.email, "password": "wrongpassword"},
    )
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "INVALID_CREDENTIALS"


@pytest.mark.asyncio
async def test_login_unknown_email(api_client: AsyncClient) -> None:
    resp = await api_client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "whatever"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_requires_auth(api_client: AsyncClient) -> None:
    resp = await api_client.get("/api/v1/me")
    assert resp.status_code == 401  # FastAPI >=0.110 HTTPBearer returns 401 for missing token


@pytest.mark.asyncio
async def test_me_returns_current_user(api_client: AsyncClient, test_user: User) -> None:
    login = await api_client.post(
        "/api/v1/auth/login",
        json={"email": test_user.email, "password": PASSWORD},
    )
    token = login.json()["access_token"]

    me = await api_client.get(
        "/api/v1/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert me.status_code == 200
    assert me.json()["email"] == test_user.email


@pytest.mark.asyncio
async def test_refresh_rotates_token(api_client: AsyncClient, test_user: User) -> None:
    login = await api_client.post(
        "/api/v1/auth/login",
        json={"email": test_user.email, "password": PASSWORD},
    )
    old_refresh = login.json()["refresh_token"]

    refresh = await api_client.post(
        "/api/v1/auth/refresh", json={"refresh_token": old_refresh}
    )
    assert refresh.status_code == 200
    body = refresh.json()
    assert "access_token" in body
    assert body["refresh_token"] != old_refresh  # rotated

    # Old refresh token must now be revoked
    second_refresh = await api_client.post(
        "/api/v1/auth/refresh", json={"refresh_token": old_refresh}
    )
    assert second_refresh.status_code == 401
    assert second_refresh.json()["error"]["code"] == "TOKEN_REVOKED"


@pytest.mark.asyncio
async def test_logout_revokes_refresh(api_client: AsyncClient, test_user: User) -> None:
    login = await api_client.post(
        "/api/v1/auth/login",
        json={"email": test_user.email, "password": PASSWORD},
    )
    access_token = login.json()["access_token"]
    refresh_token = login.json()["refresh_token"]

    logout = await api_client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert logout.status_code == 204

    # Token should now be revoked
    retry = await api_client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert retry.status_code == 401
    assert retry.json()["error"]["code"] == "TOKEN_REVOKED"
