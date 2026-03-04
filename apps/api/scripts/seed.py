"""Idempotent database seed. Run via: make seed"""

import asyncio
import logging
import uuid

from sqlalchemy import select

from api.auth.hashing import hash_password
from api.db.session import async_session_factory
from api.models import User, RefreshToken  # noqa: F401 — ensure models are registered
from api.models.user import Role
from api.settings import settings

logger = logging.getLogger(__name__)


async def seed() -> None:
    async with async_session_factory() as session:
        result = await session.execute(
            select(User).where(User.email == settings.admin_email)
        )
        existing = result.scalar_one_or_none()

        if existing:
            logger.info("Admin user already exists (%s), skipping.", settings.admin_email)
            return

        admin = User(
            id=uuid.uuid4(),
            email=settings.admin_email,
            hashed_password=hash_password(settings.admin_password),
            role=Role.admin,
            is_active=True,
        )
        session.add(admin)
        await session.commit()
        logger.info("Created admin user: %s", settings.admin_email)


if __name__ == "__main__":
    logging.basicConfig(level="INFO")
    asyncio.run(seed())
