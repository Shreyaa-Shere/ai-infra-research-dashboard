import logging
from typing import Any

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.db.session import get_session
from api.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/readyz")
async def readyz(session: AsyncSession = Depends(get_session)) -> Any:
    errors: list[str] = []

    try:
        await session.execute(text("SELECT 1"))
    except Exception as exc:
        logger.error("DB check failed", exc_info=exc)
        errors.append(f"db: {exc}")

    try:
        client = aioredis.from_url(settings.redis_url)
        await client.ping()
        await client.aclose()
    except Exception as exc:
        logger.error("Redis check failed", exc_info=exc)
        errors.append(f"redis: {exc}")

    if errors:
        return JSONResponse(
            status_code=503, content={"status": "error", "errors": errors}
        )

    return {"status": "ok"}
