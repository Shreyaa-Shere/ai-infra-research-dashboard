"""Idempotent database seed. Run via: make seed"""

import asyncio
import datetime
import logging
import uuid

from sqlalchemy import select

from api.auth.hashing import hash_password
from api.db.session import async_session_factory
from api.models import User, RefreshToken  # noqa: F401 — ensure models are registered
from api.models.company import Company, CompanyType
from api.models.datacenter_site import DatacenterSite, DatacenterStatus
from api.models.hardware_product import HardwareCategory, HardwareProduct
from api.models.user import Role
from api.settings import settings

logger = logging.getLogger(__name__)


async def seed() -> None:
    async with async_session_factory() as session:
        # ── Admin user ────────────────────────────────────────────────────────
        result = await session.execute(
            select(User).where(User.email == settings.admin_email)
        )
        existing = result.scalar_one_or_none()

        if existing:
            logger.info("Admin user already exists (%s), skipping.", settings.admin_email)
        else:
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

        # ── Companies ─────────────────────────────────────────────────────────
        companies_data = [
            {"name": "NVIDIA", "type": CompanyType.vendor, "region": "US", "website": "https://nvidia.com"},
            {"name": "AMD", "type": CompanyType.vendor, "region": "US", "website": "https://amd.com"},
            {"name": "TSMC", "type": CompanyType.fab, "region": "Asia", "website": "https://tsmc.com"},
            {"name": "Amazon", "type": CompanyType.cloud, "region": "US", "website": "https://aws.amazon.com"},
            {"name": "Google", "type": CompanyType.cloud, "region": "US", "website": "https://cloud.google.com"},
        ]

        company_map: dict[str, uuid.UUID] = {}
        for c in companies_data:
            result = await session.execute(
                select(Company).where(Company.name == c["name"])
            )
            existing_co = result.scalar_one_or_none()
            if existing_co:
                company_map[c["name"]] = existing_co.id
                logger.info("Company '%s' already exists, skipping.", c["name"])
            else:
                co = Company(id=uuid.uuid4(), **c)  # type: ignore[arg-type]
                session.add(co)
                await session.flush()
                company_map[c["name"]] = co.id
                logger.info("Created company: %s", c["name"])

        await session.commit()

        # ── Hardware Products ─────────────────────────────────────────────────
        hw_data = [
            {
                "name": "H100",
                "vendor": "NVIDIA",
                "category": HardwareCategory.GPU,
                "release_date": datetime.date(2023, 3, 22),
                "memory_gb": 80,
                "tdp_watts": 700,
                "process_node": "4nm",
                "notes": "Hopper architecture, flagship datacenter GPU.",
            },
            {
                "name": "A100",
                "vendor": "NVIDIA",
                "category": HardwareCategory.GPU,
                "release_date": datetime.date(2020, 5, 14),
                "memory_gb": 80,
                "tdp_watts": 400,
                "process_node": "7nm",
                "notes": "Ampere architecture.",
            },
            {
                "name": "MI300X",
                "vendor": "AMD",
                "category": HardwareCategory.GPU,
                "release_date": datetime.date(2023, 12, 6),
                "memory_gb": 192,
                "tdp_watts": 750,
                "process_node": "5nm",
                "notes": "CDNA3 architecture, record HBM3 memory capacity.",
            },
        ]

        for hw in hw_data:
            result = await session.execute(
                select(HardwareProduct).where(
                    HardwareProduct.name == hw["name"],
                    HardwareProduct.vendor == hw["vendor"],
                )
            )
            if result.scalar_one_or_none():
                logger.info("HardwareProduct '%s' already exists, skipping.", hw["name"])
            else:
                session.add(HardwareProduct(id=uuid.uuid4(), **hw))  # type: ignore[arg-type]
                logger.info("Created hardware product: %s", hw["name"])

        await session.commit()

        # ── Datacenter Sites ──────────────────────────────────────────────────
        dc_data = [
            {
                "name": "US West GPU Cluster",
                "region": "us-west-2",
                "owner_company_id": company_map.get("Amazon"),
                "power_mw": 500,
                "status": DatacenterStatus.active,
                "notes": "Primary AWS AI training cluster.",
            },
            {
                "name": "EU AI Datacenter",
                "region": "eu-west-1",
                "owner_company_id": company_map.get("Google"),
                "power_mw": 300,
                "status": DatacenterStatus.active,
                "notes": "Google Cloud EU AI facility.",
            },
        ]

        for dc in dc_data:
            result = await session.execute(
                select(DatacenterSite).where(DatacenterSite.name == dc["name"])
            )
            if result.scalar_one_or_none():
                logger.info("DatacenterSite '%s' already exists, skipping.", dc["name"])
            else:
                session.add(DatacenterSite(id=uuid.uuid4(), **dc))  # type: ignore[arg-type]
                logger.info("Created datacenter site: %s", dc["name"])

        await session.commit()
        logger.info("Seed complete.")


if __name__ == "__main__":
    logging.basicConfig(level="INFO")
    asyncio.run(seed())
