"""
System info endpoint — admin only.

Returns operational metrics useful for dashboards and health checks:
app version, git SHA, environment name, uptime, and dependency status.
"""

import time
from typing import Any

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.dependencies import get_current_user
from api.db.session import get_session
from api.models.user import Role, User
from api.routes.version import _git_sha
from api.schemas.errors import api_error
from api.settings import settings

router = APIRouter(tags=["system"])

_START_TIME = time.monotonic()


@router.get("/system/info")
async def system_info(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Any:
    if current_user.role != Role.admin:
        raise api_error("forbidden", "Admin access required", 403)

    # DB check
    db_ok = True
    try:
        await session.execute(text("SELECT 1"))
    except Exception:
        db_ok = False

    # Redis check
    redis_ok = True
    try:
        client = aioredis.from_url(settings.redis_url)
        await client.ping()
        await client.aclose()
    except Exception:
        redis_ok = False

    return {
        "version": settings.app_version,
        "git_sha": _git_sha(),
        "environment": settings.environment,
        "uptime_seconds": round(time.monotonic() - _START_TIME, 1),
        "db_connected": db_ok,
        "redis_connected": redis_ok,
    }
