"""Database seed script. Add initial data population logic here."""

import asyncio
import logging

logger = logging.getLogger(__name__)


async def seed() -> None:
    logger.info("Seeding database...")
    # Add seed logic here as models are created.
    logger.info("Seeding complete.")


if __name__ == "__main__":
    asyncio.run(seed())
