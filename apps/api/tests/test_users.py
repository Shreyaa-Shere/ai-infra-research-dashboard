"""
Tests for User Management (Slice 7).

Covers:
- POST /api/v1/users/invite: admin-only, creates invite, returns URL
- POST /api/v1/users/invite: 403 for non-admin
- POST /api/v1/users/invite: 409 when email already registered
- POST /api/v1/users/accept-invite: creates user, marks invite used
- POST /api/v1/users/accept-invite: 400 on invalid token
- POST /api/v1/users/accept-invite: 400 on already-used token
- GET /api/v1/users: admin-only list
- GET /api/v1/users: 403 for analyst
- PATCH /api/v1/users/{id}: admin changes role
- PATCH /api/v1/users/{id}: admin deactivates user
"""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.user import Role, User
from api.models.user_invite import UserInvite

# ── helpers ────────────────────────────────────────────────────────────────────


async def _cleanup_invites(db: AsyncSession) -> None:
    await db.execute(delete(UserInvite))
    await db.commit()


# ── invite flow ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_invite_admin_only_403(
    api_client: AsyncClient, analyst_token: str
) -> None:
    resp = await api_client.post(
        "/api/v1/users/invite",
        json={"email": "new@example.com", "role": "analyst"},
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_invite_creates_invite_url(
    api_client: AsyncClient, admin_token: str, db: AsyncSession
) -> None:
    await _cleanup_invites(db)
    resp = await api_client.post(
        "/api/v1/users/invite",
        json={"email": "invited@example.com", "role": "analyst"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "invited@example.com"
    assert data["role"] == "analyst"
    assert "invite_url" in data
    assert "token=" in data["invite_url"]
    await _cleanup_invites(db)


@pytest.mark.asyncio
async def test_invite_email_already_registered_409(
    api_client: AsyncClient, admin_token: str, admin_user: User
) -> None:
    resp = await api_client.post(
        "/api/v1/users/invite",
        json={"email": admin_user.email, "role": "analyst"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_invite_cannot_invite_admin_role(
    api_client: AsyncClient, admin_token: str
) -> None:
    resp = await api_client.post(
        "/api/v1/users/invite",
        json={"email": "newadmin@example.com", "role": "admin"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 422


# ── accept invite ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_accept_invite_creates_user(
    api_client: AsyncClient, admin_token: str, db: AsyncSession
) -> None:
    await _cleanup_invites(db)
    # Create invite
    invite_resp = await api_client.post(
        "/api/v1/users/invite",
        json={"email": "newanalyst@example.com", "role": "analyst"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert invite_resp.status_code == 201
    invite_url = invite_resp.json()["invite_url"]
    # Extract token from URL
    token = invite_url.split("token=", 1)[1]

    # Accept invite
    accept_resp = await api_client.post(
        "/api/v1/users/accept-invite",
        json={"token": token, "password": "Newpass1!"},
    )
    assert accept_resp.status_code == 201
    user_data = accept_resp.json()
    assert user_data["email"] == "newanalyst@example.com"
    assert user_data["role"] == "analyst"
    assert user_data["is_active"] is True

    # Cleanup created user
    await db.execute(delete(User).where(User.email == "newanalyst@example.com"))
    await db.commit()
    await _cleanup_invites(db)


@pytest.mark.asyncio
async def test_accept_invite_invalid_token(api_client: AsyncClient) -> None:
    resp = await api_client.post(
        "/api/v1/users/accept-invite",
        json={"token": "totally-fake-token", "password": "Newpass1!"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_accept_invite_already_used(
    api_client: AsyncClient, admin_token: str, db: AsyncSession
) -> None:
    await _cleanup_invites(db)
    invite_resp = await api_client.post(
        "/api/v1/users/invite",
        json={"email": "usedonce@example.com", "role": "viewer"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    token = invite_resp.json()["invite_url"].split("token=", 1)[1]

    # First accept — succeeds
    r1 = await api_client.post(
        "/api/v1/users/accept-invite",
        json={"token": token, "password": "Newpass1!"},
    )
    assert r1.status_code == 201

    # Second accept — fails
    r2 = await api_client.post(
        "/api/v1/users/accept-invite",
        json={"token": token, "password": "Newpass1!"},
    )
    assert r2.status_code == 400

    # Cleanup
    await db.execute(delete(User).where(User.email == "usedonce@example.com"))
    await db.commit()
    await _cleanup_invites(db)


# ── list users ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_users_admin_200(api_client: AsyncClient, admin_token: str) -> None:
    resp = await api_client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_list_users_analyst_403(
    api_client: AsyncClient, analyst_token: str
) -> None:
    resp = await api_client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert resp.status_code == 403


# ── update user ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_user_role(
    api_client: AsyncClient, admin_token: str, test_user: User, db: AsyncSession
) -> None:
    resp = await api_client.patch(
        f"/api/v1/users/{test_user.id}",
        json={"role": "analyst"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "analyst"

    # Restore
    await db.refresh(test_user)
    test_user.role = Role.viewer
    await db.commit()


@pytest.mark.asyncio
async def test_deactivate_user(
    api_client: AsyncClient, admin_token: str, db: AsyncSession
) -> None:
    # Create a throwaway user to deactivate
    from api.auth.hashing import hash_password

    email = f"deact_{uuid.uuid4().hex[:8]}@example.com"
    target = User(
        id=uuid.uuid4(),
        email=email,
        hashed_password=hash_password("Temp1234!"),
        role=Role.viewer,
        is_active=True,
    )
    db.add(target)
    await db.commit()

    resp = await api_client.patch(
        f"/api/v1/users/{target.id}",
        json={"is_active": False},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False

    # Cleanup
    await db.execute(delete(User).where(User.id == target.id))
    await db.commit()
