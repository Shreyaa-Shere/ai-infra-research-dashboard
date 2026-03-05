from __future__ import annotations

import json
import secrets
import uuid
from datetime import UTC, datetime, timedelta

import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.jwt import hash_token
from api.models.user import User
from api.repositories.note import AuditLogRepository
from api.repositories.user import UserRepository
from api.schemas.errors import api_error
from api.schemas.pagination import PaginatedResponse
from api.schemas.user import (
    AcceptInviteRequest,
    UserAdminOut,
    UserInviteCreate,
    UserInviteResponse,
    UserUpdate,
)
from api.settings import settings

_repo = UserRepository()
_audit = AuditLogRepository()


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(
        password.encode(), bcrypt.gensalt(rounds=settings.bcrypt_rounds)
    ).decode()


class UserService:
    async def invite_user(
        self,
        session: AsyncSession,
        payload: UserInviteCreate,
        actor: User,
    ) -> UserInviteResponse:
        # Check email not already registered
        existing = await _repo.get_by_email(session, payload.email)
        if existing:
            raise api_error("EMAIL_TAKEN", "A user with that email already exists", 409)

        raw_token = secrets.token_urlsafe(32)
        token_hash = hash_token(raw_token)
        expires_at = datetime.now(UTC) + timedelta(days=settings.invite_token_ttl_days)

        invite = await _repo.create_invite(
            session,
            email=payload.email,
            role=payload.role,
            token_hash=token_hash,
            expires_at=expires_at,
            created_by_user_id=actor.id,
        )

        await _audit.append(
            session,
            actor_user_id=actor.id,
            action="user.invited",
            entity_type="user_invite",
            entity_id=str(invite.id),
            meta_json=json.dumps({"email": payload.email, "role": payload.role.value}),
        )

        await session.commit()

        invite_url = f"{settings.frontend_base_url}/accept-invite?token={raw_token}"

        return UserInviteResponse(
            id=invite.id,
            email=invite.email,
            role=invite.role,
            invite_url=invite_url,
            expires_at=invite.expires_at,
            created_at=invite.created_at,
        )

    async def accept_invite(
        self,
        session: AsyncSession,
        payload: AcceptInviteRequest,
    ) -> UserAdminOut:
        token_hash = hash_token(payload.token)
        invite = await _repo.get_invite_by_token_hash(session, token_hash)

        if not invite:
            raise api_error("INVITE_INVALID", "Invalid or expired invite token", 400)
        if invite.used_at is not None:
            raise api_error("INVITE_USED", "This invite has already been used", 400)
        if invite.expires_at < datetime.now(UTC):
            raise api_error("INVITE_EXPIRED", "This invite has expired", 400)

        # Check email not already registered (race condition guard)
        existing = await _repo.get_by_email(session, invite.email)
        if existing:
            raise api_error("EMAIL_TAKEN", "A user with that email already exists", 409)

        hashed_pw = _hash_password(payload.password)
        user = await _repo.create_user(
            session,
            email=invite.email,
            hashed_password=hashed_pw,
            role=invite.role,
        )

        await _repo.mark_invite_used(session, invite)

        await _audit.append(
            session,
            actor_user_id=user.id,
            action="user.invite_accepted",
            entity_type="user",
            entity_id=str(user.id),
            meta_json=json.dumps({"email": user.email, "role": user.role.value}),
        )

        await session.commit()

        return UserAdminOut.model_validate(user)

    async def list_users(
        self,
        session: AsyncSession,
        limit: int,
        offset: int,
    ) -> PaginatedResponse[UserAdminOut]:
        users, total = await _repo.list_users(session, limit=limit, offset=offset)
        return PaginatedResponse(
            items=[UserAdminOut.model_validate(u) for u in users],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def update_user(
        self,
        session: AsyncSession,
        target_id: uuid.UUID,
        payload: UserUpdate,
        actor: User,
    ) -> UserAdminOut:
        if target_id == actor.id:
            raise api_error(
                "SELF_MODIFY", "Cannot modify your own account via this endpoint", 400
            )

        user = await _repo.get_by_id(session, target_id)
        if not user:
            raise api_error("NOT_FOUND", "User not found", 404)

        fields: dict = {}
        if payload.role is not None and payload.role != user.role:
            fields["role"] = payload.role
            await _audit.append(
                session,
                actor_user_id=actor.id,
                action="user.role_changed",
                entity_type="user",
                entity_id=str(user.id),
                meta_json=json.dumps(
                    {"old_role": user.role.value, "new_role": payload.role.value}
                ),
            )

        if payload.is_active is not None and payload.is_active != user.is_active:
            fields["is_active"] = payload.is_active
            if not payload.is_active:
                # Revoke all active refresh tokens
                await _repo.revoke_all_refresh_tokens(session, user.id)
                await _audit.append(
                    session,
                    actor_user_id=actor.id,
                    action="user.deactivated",
                    entity_type="user",
                    entity_id=str(user.id),
                    meta_json=json.dumps({"email": user.email}),
                )

        if fields:
            user = await _repo.update_user(session, user, fields)

        await session.commit()

        return UserAdminOut.model_validate(user)


_svc = UserService()
