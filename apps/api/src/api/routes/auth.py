import asyncio
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.dependencies import get_current_user
from api.auth.hashing import hash_password, verify_and_update
from api.auth.jwt import create_access_token, create_refresh_token, hash_token
from api.auth.rate_limit import limiter
from api.db.session import get_session
from api.models.refresh_token import RefreshToken
from api.models.user import User
from api.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RefreshResponse,
    TokenResponse,
    UserOut,
)
from api.schemas.errors import api_error
from api.schemas.user import ForgotPasswordRequest, ResetPasswordRequest
from api.services.user import _svc as user_svc
from api.settings import settings

router = APIRouter(prefix="/auth", tags=["auth"])

# Computed once at import time; used as fallback when app.state.dummy_hash is not set
# (e.g. in tests where the ASGI lifespan does not run via ASGITransport).
_FALLBACK_DUMMY_HASH = hash_password("no-such-user-timing-safety")


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(
    request: Request,
    body: LoginRequest,
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    result = await session.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    # Run bcrypt in a thread pool to avoid blocking the async event loop.
    # Always verify (even for missing user) to prevent timing-based enumeration.
    # verify_and_update also silently re-hashes if stored rounds are outdated.
    dummy = getattr(request.app.state, "dummy_hash", None) or _FALLBACK_DUMMY_HASH
    is_valid, new_hash = await asyncio.to_thread(
        verify_and_update, body.password, user.hashed_password if user else dummy
    )
    if not user or not is_valid:
        raise api_error("INVALID_CREDENTIALS", "Invalid email or password", 401)

    if new_hash:
        user.hashed_password = new_hash

    if not user.is_active:
        raise api_error("USER_INACTIVE", "Account is deactivated", 403)

    access_token = create_access_token(str(user.id), user.role.value)
    raw_refresh, refresh_hash = create_refresh_token()

    token = RefreshToken(
        id=uuid.uuid4(),
        user_id=user.id,
        token_hash=refresh_hash,
        expires_at=datetime.now(UTC) + timedelta(days=settings.jwt_refresh_ttl_days),
    )
    session.add(token)
    await session.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=raw_refresh,
        user=UserOut.model_validate(user),
    )


@router.post("/refresh", response_model=RefreshResponse)
async def refresh(
    body: RefreshRequest,
    session: AsyncSession = Depends(get_session),
) -> RefreshResponse:
    token_hash = hash_token(body.refresh_token)

    result = await session.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    stored = result.scalar_one_or_none()

    if not stored:
        raise api_error("INVALID_REFRESH_TOKEN", "Refresh token not found", 401)
    if stored.revoked_at is not None:
        raise api_error("TOKEN_REVOKED", "Refresh token has been revoked", 401)
    if stored.expires_at < datetime.now(UTC):
        raise api_error("TOKEN_EXPIRED", "Refresh token has expired", 401)

    # Rotate: revoke old token before issuing new one
    stored.revoked_at = datetime.now(UTC)

    user = await session.get(User, stored.user_id)
    if not user or not user.is_active:
        await session.commit()
        raise api_error("USER_INACTIVE", "User not found or deactivated", 401)

    access_token = create_access_token(str(user.id), user.role.value)
    raw_refresh, refresh_hash = create_refresh_token()

    new_token = RefreshToken(
        id=uuid.uuid4(),
        user_id=user.id,
        token_hash=refresh_hash,
        expires_at=datetime.now(UTC) + timedelta(days=settings.jwt_refresh_ttl_days),
    )
    session.add(new_token)
    await session.commit()

    return RefreshResponse(access_token=access_token, refresh_token=raw_refresh)


@router.post("/forgot-password", status_code=204)
@limiter.limit("5/minute")
async def forgot_password(
    request: Request,
    body: ForgotPasswordRequest,
    session: AsyncSession = Depends(get_session),
) -> Response:
    """
    Always responds 204 regardless of whether the email is registered.
    This prevents user-enumeration attacks.
    """
    await user_svc.forgot_password(session, body)
    return Response(status_code=204)


@router.post("/reset-password", status_code=204)
async def reset_password(
    body: ResetPasswordRequest,
    session: AsyncSession = Depends(get_session),
) -> Response:
    await user_svc.reset_password(session, body)
    return Response(status_code=204)


@router.post("/logout", status_code=204)
async def logout(
    body: LogoutRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Response:
    token_hash = hash_token(body.refresh_token)

    result = await session.execute(
        select(RefreshToken)
        .where(RefreshToken.token_hash == token_hash)
        .where(RefreshToken.user_id == current_user.id)
    )
    stored = result.scalar_one_or_none()

    if stored and stored.revoked_at is None:
        stored.revoked_at = datetime.now(UTC)
        await session.commit()

    return Response(status_code=204)
