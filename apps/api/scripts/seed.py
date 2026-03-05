"""Idempotent database seed. Run via: make seed"""

import asyncio
import datetime
import logging
import re
import uuid

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from api.auth.hashing import hash_password
from api.db.session import async_session_factory
from api.models import User, RefreshToken  # noqa: F401 — ensure models are registered
from api.models.company import Company, CompanyType
from api.models.datacenter_site import DatacenterSite, DatacenterStatus
from api.models.hardware_product import HardwareCategory, HardwareProduct
from api.models.metric import MetricEntityType, MetricFrequency, MetricPoint, MetricSeries
from api.models.research_note import EntityType, NoteEntityLink, NoteStatus, ResearchNote
from api.models.user import Role
from api.settings import settings


def _slugify(title: str, uid: uuid.UUID) -> str:
    slug = title.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_-]+", "-", slug)
    slug = slug.strip("-")
    short = str(uid).replace("-", "")[:8]
    return f"{slug}-{short}"

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

        # ── Analyst user (for seed notes author) ──────────────────────────────
        analyst_email = "analyst@example.com"
        result = await session.execute(select(User).where(User.email == analyst_email))
        analyst = result.scalar_one_or_none()
        if not analyst:
            analyst = User(
                id=uuid.uuid4(),
                email=analyst_email,
                hashed_password=hash_password("Analystpass1!"),
                role=Role.analyst,
                is_active=True,
            )
            session.add(analyst)
            await session.commit()
            await session.refresh(analyst)
            logger.info("Created analyst user: %s", analyst_email)

        # Fetch entity IDs for linking
        hw_h100 = (
            await session.execute(
                select(HardwareProduct).where(HardwareProduct.name == "H100")
            )
        ).scalar_one_or_none()

        co_nvidia = (
            await session.execute(select(Company).where(Company.name == "NVIDIA"))
        ).scalar_one_or_none()

        dc_us = (
            await session.execute(
                select(DatacenterSite).where(
                    DatacenterSite.name == "US West GPU Cluster"
                )
            )
        ).scalar_one_or_none()

        # ── Research Notes ────────────────────────────────────────────────────
        note_data = [
            {
                "title": "H100 Supply Chain Analysis",
                "body_markdown": (
                    "# H100 Supply Chain Analysis\n\n"
                    "## Overview\n\n"
                    "The NVIDIA H100 GPU represents a critical node in the AI infrastructure supply chain. "
                    "Manufactured on TSMC's 4nm process, lead times have extended to **26–52 weeks** in 2024.\n\n"
                    "## Key Constraints\n\n"
                    "- CoWoS packaging capacity at TSMC\n"
                    "- HBM3 supply from SK Hynix\n"
                    "- NVLink switch availability\n\n"
                    "## Outlook\n\n"
                    "Supply is expected to normalize by Q3 2025 as TSMC expands CoWoS capacity."
                ),
                "status": NoteStatus.published,
                "tags": ["gpu", "supply-chain", "nvidia"],
                "links": [
                    (EntityType.hardware_product, hw_h100),
                    (EntityType.company, co_nvidia),
                ],
            },
            {
                "title": "US West GPU Cluster Capacity Review",
                "body_markdown": (
                    "# US West GPU Cluster Capacity Review\n\n"
                    "## Current State\n\n"
                    "The US West GPU Cluster operates at **87% utilization** as of Q1 2026. "
                    "Primary workloads include LLM training and inference.\n\n"
                    "## Recommendations\n\n"
                    "1. Expand cooling capacity before adding more racks\n"
                    "2. Negotiate Power Purchase Agreement for 200MW additional capacity\n"
                    "3. Evaluate liquid cooling for next-gen H200 deployment"
                ),
                "status": NoteStatus.review,
                "tags": ["datacenter", "capacity"],
                "links": [(EntityType.datacenter, dc_us)],
            },
            {
                "title": "NVIDIA Competitive Moat — Draft",
                "body_markdown": (
                    "# NVIDIA Competitive Moat\n\n"
                    "_Draft — in progress_\n\n"
                    "## CUDA Ecosystem Lock-in\n\n"
                    "NVIDIA's CUDA platform has been developed since 2006 and now underpins "
                    "virtually all major ML frameworks. Switching costs are extremely high.\n\n"
                    "## TODO\n\n"
                    "- [ ] Add AMD MI300X comparison\n"
                    "- [ ] Quantify developer switching costs\n"
                    "- [ ] Interview hyperscaler buyers"
                ),
                "status": NoteStatus.draft,
                "tags": ["gpu", "competitive-analysis"],
                "links": [(EntityType.company, co_nvidia)],
            },
        ]

        for nd in note_data:
            result = await session.execute(
                select(ResearchNote).where(ResearchNote.title == nd["title"])
            )
            if result.scalar_one_or_none():
                logger.info("ResearchNote '%s' already exists, skipping.", nd["title"])
                continue

            note_id = uuid.uuid4()
            slug = (
                _slugify(nd["title"], note_id)
                if nd["status"] == NoteStatus.published
                else None
            )
            note = ResearchNote(
                id=note_id,
                title=nd["title"],
                body_markdown=nd["body_markdown"],
                status=nd["status"],
                slug=slug,
                tags=nd["tags"],
                author_id=analyst.id,
                published_at=datetime.datetime.now(tz=datetime.timezone.utc)
                if nd["status"] == NoteStatus.published
                else None,
            )
            session.add(note)
            await session.flush()

            for entity_type, entity in nd["links"]:
                if entity is not None:
                    session.add(
                        NoteEntityLink(
                            id=uuid.uuid4(),
                            note_id=note.id,
                            entity_type=entity_type,
                            entity_id=entity.id,
                        )
                    )

            logger.info("Created research note: '%s' [%s]", nd["title"], nd["status"].value)

        await session.commit()

        # ── Metric Series + Points ────────────────────────────────────────────
        # Generate 18 monthly timestamps: 2024-01 → 2025-06
        def _monthly_ts(year: int, month: int) -> datetime.datetime:
            return datetime.datetime(year, month, 1, tzinfo=datetime.timezone.utc)

        months = []
        for i in range(18):
            y, m = divmod(2024 * 12 + i, 12)
            months.append(_monthly_ts(y, m + 1))

        metric_series_data = []

        if hw_h100:
            metric_series_data.append({
                "name": "H100 Shipment Volume",
                "entity_type": MetricEntityType.hardware_product,
                "entity_id": hw_h100.id,
                "unit": "units (thousands)",
                "frequency": MetricFrequency.monthly,
                "source": "Industry estimates",
                "values": [
                    12, 15, 18, 22, 28, 35, 42, 50, 58, 65,
                    70, 74, 78, 80, 82, 83, 84, 85,
                ],
            })

        if co_nvidia:
            metric_series_data.append({
                "name": "NVIDIA Revenue",
                "entity_type": MetricEntityType.company,
                "entity_id": co_nvidia.id,
                "unit": "USD billions",
                "frequency": MetricFrequency.monthly,
                "source": "Public filings (quarterly, annualized)",
                "values": [
                    6.1, 7.2, 9.0, 10.3, 11.8, 13.5, 15.2, 17.8, 19.1, 20.4,
                    22.1, 23.5, 24.9, 26.0, 27.2, 28.5, 29.0, 29.8,
                ],
            })

        if dc_us:
            metric_series_data.append({
                "name": "US West DC Power Usage",
                "entity_type": MetricEntityType.datacenter,
                "entity_id": dc_us.id,
                "unit": "MW",
                "frequency": MetricFrequency.monthly,
                "source": "Internal telemetry",
                "values": [
                    320, 335, 348, 362, 378, 390, 405, 420, 434, 445,
                    455, 462, 468, 472, 476, 479, 481, 483,
                ],
            })

        dc_eu = (
            await session.execute(
                select(DatacenterSite).where(
                    DatacenterSite.name == "EU AI Datacenter"
                )
            )
        ).scalar_one_or_none()

        if dc_eu:
            metric_series_data.append({
                "name": "EU AI DC Power Usage",
                "entity_type": MetricEntityType.datacenter,
                "entity_id": dc_eu.id,
                "unit": "MW",
                "frequency": MetricFrequency.monthly,
                "source": "Internal telemetry",
                "values": [
                    180, 188, 195, 202, 210, 217, 224, 230, 237, 243,
                    248, 252, 256, 259, 261, 263, 265, 267,
                ],
            })

        for ms_data in metric_series_data:
            existing_series = (
                await session.execute(
                    select(MetricSeries).where(
                        MetricSeries.name == ms_data["name"],
                        MetricSeries.entity_id == ms_data["entity_id"],
                    )
                )
            ).scalar_one_or_none()

            if existing_series:
                logger.info("MetricSeries '%s' already exists, skipping.", ms_data["name"])
                continue

            series = MetricSeries(
                id=uuid.uuid4(),
                name=ms_data["name"],
                entity_type=ms_data["entity_type"],
                entity_id=ms_data["entity_id"],
                unit=ms_data["unit"],
                frequency=ms_data["frequency"],
                source=ms_data["source"],
            )
            session.add(series)
            await session.flush()

            # Bulk upsert 18 monthly points
            rows = [
                {
                    "id": uuid.uuid4(),
                    "metric_series_id": series.id,
                    "timestamp": ts,
                    "value": float(val),
                }
                for ts, val in zip(months, ms_data["values"])
            ]
            stmt = pg_insert(MetricPoint).values(rows)
            stmt = stmt.on_conflict_do_update(
                constraint="uq_metric_point",
                set_={"value": stmt.excluded.value},
            )
            await session.execute(stmt)
            logger.info(
                "Created MetricSeries '%s' with %d points.",
                ms_data["name"],
                len(rows),
            )

        await session.commit()
        logger.info("Seed complete.")


if __name__ == "__main__":
    logging.basicConfig(level="INFO")
    asyncio.run(seed())
