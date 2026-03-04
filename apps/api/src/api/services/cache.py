from __future__ import annotations

import redis.asyncio as aioredis

from api.settings import settings

_redis: aioredis.Redis | None = None  # type: ignore[type-arg]


async def get_redis() -> aioredis.Redis:  # type: ignore[type-arg]
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis


async def cache_get(key: str) -> str | None:
    r = await get_redis()
    value: str | None = await r.get(key)
    return value


async def cache_set(key: str, value: str, ttl: int = 60) -> None:
    r = await get_redis()
    await r.set(key, value, ex=ttl)


async def cache_delete_pattern(pattern: str) -> None:
    """Delete all keys matching a glob pattern (e.g. 'hw:list:*')."""
    r = await get_redis()
    keys = await r.keys(pattern)
    if keys:
        await r.delete(*keys)
