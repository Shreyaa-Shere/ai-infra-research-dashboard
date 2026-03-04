"""
Shared test fixtures.

Tests run inside Docker against the real PostgreSQL database (same DB as the
app). Each fixture that creates data is responsible for cleaning it up.
Tables are created via Alembic (`make migrate`) before running tests.
"""

import os
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from api.auth.hashing import hash_password
from api.main import app
from api.models import RefreshToken  # noqa: F401
from api.models.user import Role, User
from api.models.company import Company, CompanyType
from api.models.hardware_product import HardwareCategory, HardwareProduct

_DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@postgres:5432/airesearch",
)

# NullPool: no connection pooling — each session gets a fresh TCP connection
# that is closed on exit. This prevents cross-event-loop connection reuse,
# which would cause asyncpg InterfaceError / Task-pending failures.
_engine = create_async_engine(_DB_URL, poolclass=NullPool)
_SessionLocal = async_sessionmaker(_engine, expire_on_commit=False)


# ── Session-level patch: replace the app's pooled engine with NullPool ────────
# The app's own engine (api/db/engine.py) uses a connection pool. With
# function-scoped event loops, pool connections from loop N are invalid in
# loop N+1 and cause hangs/Task-pending errors. Replacing it with a NullPool
# engine for the whole test session fixes this without touching production code.

@pytest.fixture(scope="session", autouse=True)
def patch_app_db_to_nullpool() -> None:
    import api.db.engine as engine_module
    import api.db.session as session_module

    test_engine = create_async_engine(_DB_URL, poolclass=NullPool)
    engine_module.engine = test_engine
    session_module.async_session_factory = async_sessionmaker(
        test_engine, expire_on_commit=False
    )
    yield
    # No async cleanup needed — NullPool connections are closed per-session.


# ── Per-test setup: reset slowapi in-memory rate-limit counters ───────────────
# The login endpoint is limited to 10/minute. All test requests originate from
# 127.0.0.1, so the counter accumulates across tests and starts returning 429.
# Resetting MemoryStorage before each test keeps the counter at zero.

@pytest.fixture(autouse=True)
def reset_rate_limiter() -> None:
    from api.auth.rate_limit import limiter
    limiter._storage.reset()
    yield


# ── Per-test teardown: close the Redis singleton ──────────────────────────────
# The cache module holds a global _redis client. If a test triggers caching,
# Redis opens an asyncio connection. When the test's event loop closes before
# that connection is cleanly shut down, the pending read task causes
# "RuntimeError: Task pending". Closing it after every test prevents this.

@pytest_asyncio.fixture(autouse=True)
async def close_redis_after_test() -> None:
    yield
    import api.services.cache as cache_module
    if cache_module._redis is not None:
        try:
            await cache_module._redis.aclose()
        except Exception:
            pass
        cache_module._redis = None


# ── Core fixtures ─────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def db() -> AsyncSession:
    async with _SessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def api_client() -> AsyncClient:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


@pytest_asyncio.fixture
async def test_user(db: AsyncSession) -> User:
    """Create a viewer user; delete it (and its tokens) after the test."""
    email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    user = User(
        id=uuid.uuid4(),
        email=email,
        hashed_password=hash_password("Testpassword1!"),
        role=Role.viewer,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    yield user

    # Cleanup: refresh tokens first (FK), then user
    from sqlalchemy import delete

    await db.execute(delete(RefreshToken).where(RefreshToken.user_id == user.id))
    await db.execute(delete(User).where(User.id == user.id))
    await db.commit()


@pytest_asyncio.fixture
async def admin_user(db: AsyncSession) -> User:
    """Create an admin user; delete after test."""
    email = f"admin_{uuid.uuid4().hex[:8]}@example.com"
    user = User(
        id=uuid.uuid4(),
        email=email,
        hashed_password=hash_password("Adminpass1!"),
        role=Role.admin,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    yield user
    from sqlalchemy import delete
    await db.execute(delete(RefreshToken).where(RefreshToken.user_id == user.id))
    await db.execute(delete(User).where(User.id == user.id))
    await db.commit()


@pytest_asyncio.fixture
async def analyst_user(db: AsyncSession) -> User:
    """Create an analyst user; delete after test."""
    email = f"analyst_{uuid.uuid4().hex[:8]}@example.com"
    user = User(
        id=uuid.uuid4(),
        email=email,
        hashed_password=hash_password("Analystpass1!"),
        role=Role.analyst,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    yield user
    from sqlalchemy import delete
    await db.execute(delete(RefreshToken).where(RefreshToken.user_id == user.id))
    await db.execute(delete(User).where(User.id == user.id))
    await db.commit()


@pytest_asyncio.fixture
async def admin_token(api_client: AsyncClient, admin_user: User) -> str:
    resp = await api_client.post(
        "/api/v1/auth/login",
        json={"email": admin_user.email, "password": "Adminpass1!"},
    )
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def analyst_token(api_client: AsyncClient, analyst_user: User) -> str:
    resp = await api_client.post(
        "/api/v1/auth/login",
        json={"email": analyst_user.email, "password": "Analystpass1!"},
    )
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def viewer_token(api_client: AsyncClient, test_user: User) -> str:
    resp = await api_client.post(
        "/api/v1/auth/login",
        json={"email": test_user.email, "password": "Testpassword1!"},
    )
    return resp.json()["access_token"]
