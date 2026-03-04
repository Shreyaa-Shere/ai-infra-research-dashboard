import uuid

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.jwt import decode_access_token
from api.db.session import get_session
from api.models.user import User
from api.schemas.errors import api_error

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
    except jwt.ExpiredSignatureError:
        raise api_error("TOKEN_EXPIRED", "Access token has expired", 401)
    except jwt.InvalidTokenError:
        raise api_error("INVALID_TOKEN", "Invalid access token", 401)

    user_id_str: str | None = payload.get("sub")
    if not user_id_str:
        raise api_error("INVALID_TOKEN", "Malformed token payload", 401)

    user = await session.get(User, uuid.UUID(user_id_str))
    if not user or not user.is_active:
        raise api_error("USER_INACTIVE", "User not found or deactivated", 401)

    return user


def require_role(roles: list[str]):
    """Dependency factory. Usage: Depends(require_role(['admin']))"""

    async def _check(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role.value not in roles:
            raise api_error("FORBIDDEN", "Insufficient permissions", 403)
        return current_user

    return _check
