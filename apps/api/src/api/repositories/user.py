from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.refresh_token import RefreshToken
from api.models.user import Role, User
from api.models.user_invite import UserInvite


class UserRepository:
    # ── users ─────────────────────────────────────────────────────────────────

    async def get_by_email(self, session: AsyncSession, email: str) -> User | None:
        result = await session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_id(self, session: AsyncSession, user_id: uuid.UUID) -> User | None:
        return await session.get(User, user_id)

    async def create_user(
        self,
        session: AsyncSession,
        email: str,
        hashed_password: str,
        role: Role,
    ) -> User:
        user = User(
            id=uuid.uuid4(),
            email=email,
            hashed_password=hashed_password,
            role=role,
            is_active=True,
        )
        session.add(user)
        await session.flush()
        await session.refresh(user)
        return user

    async def list_users(
        self,
        session: AsyncSession,
        limit: int,
        offset: int,
    ) -> tuple[list[User], int]:
        count = (
            await session.execute(select(func.count()).select_from(User))
        ).scalar_one()
        rows = (
            (
                await session.execute(
                    select(User)
                    .order_by(User.created_at.asc())
                    .limit(limit)
                    .offset(offset)
                )
            )
            .scalars()
            .all()
        )
        return list(rows), count

    async def update_user(
        self,
        session: AsyncSession,
        user: User,
        fields: dict,
    ) -> User:
        for k, v in fields.items():
            setattr(user, k, v)
        await session.flush()
        await session.refresh(user)
        return user

    # ── refresh tokens ────────────────────────────────────────────────────────

    async def revoke_all_refresh_tokens(
        self, session: AsyncSession, user_id: uuid.UUID
    ) -> None:
        now = datetime.now(UTC)
        await session.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .where(RefreshToken.revoked_at.is_(None))
            .values(revoked_at=now)
        )

    # ── invites ───────────────────────────────────────────────────────────────

    async def create_invite(
        self,
        session: AsyncSession,
        email: str,
        role: Role,
        token_hash: str,
        expires_at: datetime,
        created_by_user_id: uuid.UUID,
    ) -> UserInvite:
        invite = UserInvite(
            id=uuid.uuid4(),
            email=email,
            role=role,
            token_hash=token_hash,
            expires_at=expires_at,
            created_by_user_id=created_by_user_id,
        )
        session.add(invite)
        await session.flush()
        await session.refresh(invite)
        return invite

    async def get_invite_by_token_hash(
        self, session: AsyncSession, token_hash: str
    ) -> UserInvite | None:
        result = await session.execute(
            select(UserInvite).where(UserInvite.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def mark_invite_used(self, session: AsyncSession, invite: UserInvite) -> None:
        invite.used_at = datetime.now(UTC)
        await session.flush()
