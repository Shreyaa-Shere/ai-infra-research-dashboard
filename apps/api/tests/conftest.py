"""
Shared test fixtures.

Tests run inside Docker against the real PostgreSQL database (same DB as the
app). Each fixture that creates data is responsible for cleaning it up.
Tables are created via Alembic (`make migrate`) before running tests.
"""

import os
import uuid

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

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

_engine = create_async_engine(_DB_URL)
_SessionLocal = async_sessionmaker(_engine, expire_on_commit=False)


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
