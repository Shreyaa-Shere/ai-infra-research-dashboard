"""Idempotent database seed. Run via: python scripts/seed.py"""

import asyncio
import datetime
import hashlib
import logging
import re
import uuid

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from api.auth.hashing import hash_password
from api.db.session import async_session_factory
from api.models import User, RefreshToken  # noqa: F401 — ensure models are registered
from api.models.company import Company, CompanyType
from api.models.source_document import IngestionRun, IngestionStatus, RunStatus, SourceDocument, SourceEntityLink, SourceType
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


async def _get_or_skip(session, model, **where):
    """Return existing row or None (caller decides whether to insert)."""
    conditions = [getattr(model, k) == v for k, v in where.items()]
    result = await session.execute(select(model).where(*conditions))
    return result.scalar_one_or_none()


async def seed() -> None:
    async with async_session_factory() as session:
        # ── Admin user ────────────────────────────────────────────────────────
        existing = await _get_or_skip(session, User, email=settings.admin_email)
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

        # ── Analyst user ───────────────────────────────────────────────────────
        analyst_email = "analyst@example.com"
        analyst = await _get_or_skip(session, User, email=analyst_email)
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

        # ── Viewer user ────────────────────────────────────────────────────────
        viewer_email = "viewer@example.com"
        viewer = await _get_or_skip(session, User, email=viewer_email)
        if not viewer:
            viewer = User(
                id=uuid.uuid4(),
                email=viewer_email,
                hashed_password=hash_password("Viewerpass1!"),
                role=Role.viewer,
                is_active=True,
            )
            session.add(viewer)
            await session.commit()
            logger.info("Created viewer user: %s", viewer_email)

        # ── Companies ─────────────────────────────────────────────────────────
        companies_data = [
            {"name": "NVIDIA", "type": CompanyType.vendor, "region": "US", "website": "https://nvidia.com"},
            {"name": "AMD", "type": CompanyType.vendor, "region": "US", "website": "https://amd.com"},
            {"name": "Intel", "type": CompanyType.idm, "region": "US", "website": "https://intel.com"},
            {"name": "TSMC", "type": CompanyType.fab, "region": "Asia", "website": "https://tsmc.com"},
            {"name": "Samsung Foundry", "type": CompanyType.fab, "region": "Asia", "website": "https://semiconductor.samsung.com"},
            {"name": "Amazon", "type": CompanyType.cloud, "region": "US", "website": "https://aws.amazon.com"},
            {"name": "Google", "type": CompanyType.cloud, "region": "US", "website": "https://cloud.google.com"},
            {"name": "Microsoft", "type": CompanyType.cloud, "region": "US", "website": "https://azure.microsoft.com"},
            {"name": "Meta", "type": CompanyType.cloud, "region": "US", "website": "https://ai.meta.com"},
            {"name": "CoreWeave", "type": CompanyType.cloud, "region": "US", "website": "https://coreweave.com"},
            {"name": "Oracle", "type": CompanyType.cloud, "region": "US", "website": "https://oracle.com/cloud"},
            {"name": "Anthropic", "type": CompanyType.research, "region": "US", "website": "https://anthropic.com"},
            {"name": "OpenAI", "type": CompanyType.research, "region": "US", "website": "https://openai.com"},
        ]

        company_map: dict[str, uuid.UUID] = {}
        for c in companies_data:
            existing_co = await _get_or_skip(session, Company, name=c["name"])
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
                "name": "H200",
                "vendor": "NVIDIA",
                "category": HardwareCategory.GPU,
                "release_date": datetime.date(2024, 3, 18),
                "memory_gb": 141,
                "tdp_watts": 700,
                "process_node": "4nm",
                "notes": "Hopper architecture with HBM3e, 1.4x faster inference than H100.",
            },
            {
                "name": "B100",
                "vendor": "NVIDIA",
                "category": HardwareCategory.GPU,
                "release_date": datetime.date(2024, 11, 1),
                "memory_gb": 192,
                "tdp_watts": 1000,
                "process_node": "3nm",
                "notes": "Blackwell architecture, 2.5x faster training than H100.",
            },
            {
                "name": "GB200 NVL72",
                "vendor": "NVIDIA",
                "category": HardwareCategory.Accelerator,
                "release_date": datetime.date(2025, 1, 15),
                "memory_gb": 384,
                "tdp_watts": 2700,
                "process_node": "3nm",
                "notes": "Blackwell GPU + Grace CPU combo, 72-GPU rack-scale system.",
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
            {
                "name": "MI325X",
                "vendor": "AMD",
                "category": HardwareCategory.GPU,
                "release_date": datetime.date(2024, 10, 10),
                "memory_gb": 256,
                "tdp_watts": 750,
                "process_node": "5nm",
                "notes": "CDNA3 with HBM3e, improved memory bandwidth over MI300X.",
            },
            {
                "name": "Gaudi 3",
                "vendor": "Intel",
                "category": HardwareCategory.Accelerator,
                "release_date": datetime.date(2024, 4, 9),
                "memory_gb": 128,
                "tdp_watts": 900,
                "process_node": "5nm",
                "notes": "Intel AI accelerator for LLM training and inference.",
            },
            {
                "name": "TPU v5e",
                "vendor": "Google",
                "category": HardwareCategory.Accelerator,
                "release_date": datetime.date(2023, 8, 29),
                "memory_gb": 16,
                "tdp_watts": 170,
                "process_node": "7nm",
                "notes": "Google Cloud TPU v5e for efficient inference workloads.",
            },
            {
                "name": "TPU v5p",
                "vendor": "Google",
                "category": HardwareCategory.Accelerator,
                "release_date": datetime.date(2023, 12, 7),
                "memory_gb": 95,
                "tdp_watts": 600,
                "process_node": "5nm",
                "notes": "Google Cloud TPU v5p for large-scale model training.",
            },
            {
                "name": "Trainium 2",
                "vendor": "Amazon",
                "category": HardwareCategory.Accelerator,
                "release_date": datetime.date(2024, 11, 20),
                "memory_gb": 96,
                "tdp_watts": 700,
                "process_node": "3nm",
                "notes": "AWS custom training accelerator, 4x faster than Trainium 1.",
            },
            {
                "name": "InfiniBand NDR400",
                "vendor": "NVIDIA",
                "category": HardwareCategory.Networking,
                "release_date": datetime.date(2022, 11, 14),
                "memory_gb": None,
                "tdp_watts": 60,
                "process_node": None,
                "notes": "400Gb/s InfiniBand networking for GPU cluster interconnects.",
            },
            {
                "name": "Xeon Platinum 8592+",
                "vendor": "Intel",
                "category": HardwareCategory.CPU,
                "release_date": datetime.date(2024, 1, 9),
                "memory_gb": None,
                "tdp_watts": 350,
                "process_node": "Intel 3",
                "notes": "60-core Emerald Rapids Xeon for AI server platforms.",
            },
        ]

        hw_map: dict[str, uuid.UUID] = {}
        for hw in hw_data:
            existing_hw = await _get_or_skip(session, HardwareProduct, name=hw["name"], vendor=hw["vendor"])
            if existing_hw:
                hw_map[hw["name"]] = existing_hw.id
                logger.info("HardwareProduct '%s' already exists, skipping.", hw["name"])
            else:
                hw_obj = HardwareProduct(id=uuid.uuid4(), **hw)  # type: ignore[arg-type]
                session.add(hw_obj)
                await session.flush()
                hw_map[hw["name"]] = hw_obj.id
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
            {
                "name": "Azure East US AI Hub",
                "region": "us-east-1",
                "owner_company_id": company_map.get("Microsoft"),
                "power_mw": 650,
                "status": DatacenterStatus.active,
                "notes": "Microsoft Azure primary AI training facility, H100 and B100 clusters.",
            },
            {
                "name": "CoreWeave Chicago",
                "region": "us-central-1",
                "owner_company_id": company_map.get("CoreWeave"),
                "power_mw": 180,
                "status": DatacenterStatus.active,
                "notes": "CoreWeave GPU cloud, specializing in H100 bare-metal rental.",
            },
            {
                "name": "Meta AI Texas Campus",
                "region": "us-south-1",
                "owner_company_id": company_map.get("Meta"),
                "power_mw": 800,
                "status": DatacenterStatus.active,
                "notes": "Meta's dedicated AI training campus for Llama models.",
            },
            {
                "name": "Oracle OCI AI Cluster",
                "region": "us-west-1",
                "owner_company_id": company_map.get("Oracle"),
                "power_mw": 250,
                "status": DatacenterStatus.active,
                "notes": "Oracle Cloud Infrastructure 65,000-GPU H100 supercluster.",
            },
            {
                "name": "Google TPU v5 Pod",
                "region": "us-central-1",
                "owner_company_id": company_map.get("Google"),
                "power_mw": 120,
                "status": DatacenterStatus.active,
                "notes": "Dedicated TPU v5p training pod for Gemini models.",
            },
            {
                "name": "NVIDIA DGX Cloud Singapore",
                "region": "ap-southeast-1",
                "owner_company_id": company_map.get("NVIDIA"),
                "power_mw": 90,
                "status": DatacenterStatus.planned,
                "notes": "NVIDIA DGX Cloud expansion into Southeast Asia.",
            },
        ]

        dc_map: dict[str, uuid.UUID] = {}
        for dc in dc_data:
            existing_dc = await _get_or_skip(session, DatacenterSite, name=dc["name"])
            if existing_dc:
                dc_map[dc["name"]] = existing_dc.id
                logger.info("DatacenterSite '%s' already exists, skipping.", dc["name"])
            else:
                dc_obj = DatacenterSite(id=uuid.uuid4(), **dc)  # type: ignore[arg-type]
                session.add(dc_obj)
                await session.flush()
                dc_map[dc["name"]] = dc_obj.id
                logger.info("Created datacenter site: %s", dc["name"])

        await session.commit()

        # ── Re-fetch entities for note linking ────────────────────────────────
        hw_h100 = await _get_or_skip(session, HardwareProduct, name="H100", vendor="NVIDIA")
        hw_h200 = await _get_or_skip(session, HardwareProduct, name="H200", vendor="NVIDIA")
        hw_b100 = await _get_or_skip(session, HardwareProduct, name="B100", vendor="NVIDIA")
        hw_mi300x = await _get_or_skip(session, HardwareProduct, name="MI300X", vendor="AMD")
        hw_gaudi3 = await _get_or_skip(session, HardwareProduct, name="Gaudi 3", vendor="Intel")
        hw_tpu5p = await _get_or_skip(session, HardwareProduct, name="TPU v5p", vendor="Google")
        hw_trainium2 = await _get_or_skip(session, HardwareProduct, name="Trainium 2", vendor="Amazon")

        co_nvidia = await _get_or_skip(session, Company, name="NVIDIA")
        co_amd = await _get_or_skip(session, Company, name="AMD")
        co_intel = await _get_or_skip(session, Company, name="Intel")
        co_google = await _get_or_skip(session, Company, name="Google")
        co_microsoft = await _get_or_skip(session, Company, name="Microsoft")
        co_meta = await _get_or_skip(session, Company, name="Meta")
        co_tsmc = await _get_or_skip(session, Company, name="TSMC")
        co_coreweave = await _get_or_skip(session, Company, name="CoreWeave")
        co_amazon = await _get_or_skip(session, Company, name="Amazon")

        dc_us = await _get_or_skip(session, DatacenterSite, name="US West GPU Cluster")
        dc_eu = await _get_or_skip(session, DatacenterSite, name="EU AI Datacenter")
        dc_azure = await _get_or_skip(session, DatacenterSite, name="Azure East US AI Hub")
        dc_coreweave = await _get_or_skip(session, DatacenterSite, name="CoreWeave Chicago")
        dc_meta = await _get_or_skip(session, DatacenterSite, name="Meta AI Texas Campus")
        dc_oracle = await _get_or_skip(session, DatacenterSite, name="Oracle OCI AI Cluster")

        now = datetime.datetime.now(tz=datetime.timezone.utc)

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
                    (EntityType.company, co_tsmc),
                ],
                "author": analyst,
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
                "author": analyst,
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
                "author": analyst,
            },
            {
                "title": "H200 vs B100: Architectural Comparison",
                "body_markdown": (
                    "# H200 vs B100: Architectural Comparison\n\n"
                    "## Summary\n\n"
                    "Both the H200 and B100 are NVIDIA datacenter GPUs targeting large-scale AI workloads, "
                    "but differ significantly in architecture generation and use case.\n\n"
                    "## H200 (Hopper + HBM3e)\n\n"
                    "- 141GB HBM3e memory (vs 80GB HBM3 in H100)\n"
                    "- ~1.4x faster inference throughput vs H100\n"
                    "- Drop-in upgrade for H100 NVL systems\n"
                    "- Available Q1 2024\n\n"
                    "## B100 (Blackwell)\n\n"
                    "- 192GB HBM3e, 3nm process\n"
                    "- 2.5x training throughput vs H100\n"
                    "- FP4 support for aggressive quantization\n"
                    "- Requires new GB200 NVLink chassis\n\n"
                    "## Recommendation\n\n"
                    "H200 is the near-term upgrade path. B100/GB200 targets 2025+ new builds."
                ),
                "status": NoteStatus.published,
                "tags": ["gpu", "comparison", "nvidia", "blackwell"],
                "links": [
                    (EntityType.hardware_product, hw_h200),
                    (EntityType.hardware_product, hw_b100),
                    (EntityType.company, co_nvidia),
                ],
                "author": analyst,
            },
            {
                "title": "AMD MI300X Market Penetration Analysis",
                "body_markdown": (
                    "# AMD MI300X Market Penetration Analysis\n\n"
                    "## Market Position\n\n"
                    "The AMD MI300X has become the first credible alternative to NVIDIA H100 for "
                    "LLM inference workloads, driven by its **192GB HBM3** capacity.\n\n"
                    "## Key Wins\n\n"
                    "- Microsoft Azure: MI300X deployed in Azure ND MI300X series\n"
                    "- Meta: Evaluating for inference serving\n"
                    "- Oracle: Available via OCI\n\n"
                    "## CUDA vs ROCm\n\n"
                    "ROCm 6.0 significantly closes the software gap. PyTorch, vLLM, and "
                    "llama.cpp all support MI300X natively.\n\n"
                    "## Financial Impact\n\n"
                    "AMD data center revenue grew 400% YoY in Q3 2024, largely driven by MI300X."
                ),
                "status": NoteStatus.published,
                "tags": ["gpu", "amd", "competitive-analysis", "market-share"],
                "links": [
                    (EntityType.hardware_product, hw_mi300x),
                    (EntityType.company, co_amd),
                    (EntityType.company, co_microsoft),
                ],
                "author": analyst,
            },
            {
                "title": "Hyperscaler CapEx Trends 2025–2026",
                "body_markdown": (
                    "# Hyperscaler CapEx Trends 2025–2026\n\n"
                    "## Overview\n\n"
                    "Combined CapEx from the Big Four cloud providers is projected to exceed "
                    "**$300 billion** in 2025, with AI infrastructure representing ~60% of spend.\n\n"
                    "## By Provider\n\n"
                    "| Provider | 2024 CapEx | 2025 Guidance |\n"
                    "|----------|------------|---------------|\n"
                    "| Microsoft | $55B | $80B |\n"
                    "| Google | $52B | $75B |\n"
                    "| Amazon | $75B | $100B+ |\n"
                    "| Meta | $38B | $60–65B |\n\n"
                    "## Key Drivers\n\n"
                    "- LLM training clusters (B100/GB200)\n"
                    "- Inference scaling (H200, MI300X)\n"
                    "- Power and cooling infrastructure\n\n"
                    "## Risks\n\n"
                    "Power procurement remains the binding constraint in the US market."
                ),
                "status": NoteStatus.review,
                "tags": ["datacenter", "capex", "cloud"],
                "links": [
                    (EntityType.company, co_microsoft),
                    (EntityType.company, co_google),
                    (EntityType.company, co_amazon),
                    (EntityType.company, co_meta),
                ],
                "author": analyst,
            },
            {
                "title": "Intel Gaudi 3 Competitive Assessment",
                "body_markdown": (
                    "# Intel Gaudi 3 Competitive Assessment\n\n"
                    "## Product Overview\n\n"
                    "Intel Gaudi 3 targets LLM inference and training as a lower-cost alternative "
                    "to NVIDIA H100. Built on TSMC 5nm, it offers 128GB HBM2e.\n\n"
                    "## Benchmark Results (preliminary)\n\n"
                    "- Llama 3 70B inference: ~1.5x H100 throughput claimed\n"
                    "- Training: parity with H100 on select workloads\n"
                    "- Memory bandwidth: 3.7 TB/s vs H100 3.35 TB/s\n\n"
                    "## Software Ecosystem\n\n"
                    "Intel Gaudi software stack (SynapseAI) lags CUDA significantly. "
                    "Limited support for newer frameworks.\n\n"
                    "## Verdict\n\n"
                    "Gaudi 3 is compelling on price/performance but software maturity is a risk."
                ),
                "status": NoteStatus.draft,
                "tags": ["gpu", "intel", "benchmark", "competitive-analysis"],
                "links": [
                    (EntityType.hardware_product, hw_gaudi3),
                    (EntityType.company, co_intel),
                ],
                "author": analyst,
            },
            {
                "title": "TSMC CoWoS Capacity Expansion Plan",
                "body_markdown": (
                    "# TSMC CoWoS Capacity Expansion Plan\n\n"
                    "## Background\n\n"
                    "Chip-on-Wafer-on-Substrate (CoWoS) packaging is the bottleneck for "
                    "advanced AI GPU production. All H100, H200, B100, and MI300X chips require it.\n\n"
                    "## 2024–2026 Expansion\n\n"
                    "TSMC has committed to tripling CoWoS capacity by end of 2025:\n"
                    "- Current (2024): ~35,000 wafers/month\n"
                    "- Target (2025 Q4): ~100,000 wafers/month\n\n"
                    "## New Sites\n\n"
                    "- TSMC Hsinchu Fab 21P: CoWoS-L production\n"
                    "- TSMC Taichung: CoWoS-S capacity\n\n"
                    "## Investment\n\n"
                    "Total packaging CapEx estimated at $10B through 2026."
                ),
                "status": NoteStatus.published,
                "tags": ["manufacturing", "supply-chain", "tsmc"],
                "links": [
                    (EntityType.company, co_tsmc),
                    (EntityType.hardware_product, hw_h100),
                    (EntityType.hardware_product, hw_b100),
                ],
                "author": analyst,
            },
            {
                "title": "CoreWeave GPU Cloud Infrastructure Review",
                "body_markdown": (
                    "# CoreWeave GPU Cloud Infrastructure Review\n\n"
                    "## Company Overview\n\n"
                    "CoreWeave has emerged as the leading GPU-specialized cloud provider, "
                    "focusing exclusively on GPU workloads. IPO in Q1 2025 valued at ~$23B.\n\n"
                    "## Infrastructure\n\n"
                    "- ~45,000 NVIDIA H100 GPUs deployed\n"
                    "- InfiniBand NDR400 interconnects throughout\n"
                    "- 32 data centers across US and Europe\n\n"
                    "## Key Customers\n\n"
                    "- Microsoft (major investor and customer)\n"
                    "- Meta\n"
                    "- Various AI startups\n\n"
                    "## Competitive Position\n\n"
                    "CoreWeave offers faster GPU availability and better networking than hyperscalers "
                    "for pure training workloads."
                ),
                "status": NoteStatus.published,
                "tags": ["cloud", "gpu", "infrastructure"],
                "links": [
                    (EntityType.company, co_coreweave),
                    (EntityType.datacenter, dc_coreweave),
                ],
                "author": analyst,
            },
            {
                "title": "Google TPU v5p vs NVIDIA H100 Training Comparison",
                "body_markdown": (
                    "# Google TPU v5p vs NVIDIA H100 Training Comparison\n\n"
                    "## Overview\n\n"
                    "Google's TPU v5p represents their most powerful training accelerator, "
                    "designed to challenge NVIDIA dominance for large model training.\n\n"
                    "## Specifications Comparison\n\n"
                    "| Metric | TPU v5p | H100 |\n"
                    "|--------|---------|------|\n"
                    "| Memory | 95GB HBM2e | 80GB HBM3 |\n"
                    "| BF16 TFLOPS | 459 | 989 |\n"
                    "| Interconnect | 4800 Gbps ICI | 900 GB/s NVLink |\n"
                    "| Power | 600W | 700W |\n\n"
                    "## Workload Suitability\n\n"
                    "TPU v5p excels on JAX-based workloads and Google-native frameworks. "
                    "NVIDIA H100 wins for general PyTorch workloads.\n\n"
                    "## Conclusion\n\n"
                    "TPU v5p is highly competitive for JAX/TensorFlow shops but limited outside GCP."
                ),
                "status": NoteStatus.review,
                "tags": ["gpu", "tpu", "comparison", "google", "training"],
                "links": [
                    (EntityType.hardware_product, hw_tpu5p),
                    (EntityType.hardware_product, hw_h100),
                    (EntityType.company, co_google),
                ],
                "author": analyst,
            },
            {
                "title": "AI Data Center Power Consumption Crisis",
                "body_markdown": (
                    "# AI Data Center Power Consumption Crisis\n\n"
                    "## The Problem\n\n"
                    "AI training clusters are consuming power at unprecedented scale. "
                    "A single GB200 NVL72 rack draws **120kW**. A 10,000-GPU cluster "
                    "requires approximately **1.2 GW** of power — equivalent to a nuclear reactor.\n\n"
                    "## Grid Impact\n\n"
                    "- US grid operators report AI-driven load growth of 15-20% annually\n"
                    "- Power Purchase Agreements (PPAs) for new data centers now 5-10 year lock-ins\n"
                    "- Water cooling requirements create environmental concerns\n\n"
                    "## Solutions Being Pursued\n\n"
                    "1. **Liquid cooling**: Direct liquid cooling at chip level\n"
                    "2. **Nuclear partnerships**: Microsoft, Amazon signing nuclear PPAs\n"
                    "3. **Geography shifts**: Locating facilities near hydro/wind resources\n"
                    "4. **Efficiency gains**: FP4/FP8 inference to reduce compute per query\n\n"
                    "## Investment Implications\n\n"
                    "Power infrastructure, cooling technology, and grid equipment companies "
                    "are significant beneficiaries of the AI buildout."
                ),
                "status": NoteStatus.published,
                "tags": ["datacenter", "power", "sustainability", "infrastructure"],
                "links": [
                    (EntityType.datacenter, dc_us),
                    (EntityType.datacenter, dc_azure),
                    (EntityType.datacenter, dc_meta),
                    (EntityType.company, co_amazon),
                    (EntityType.company, co_microsoft),
                ],
                "author": analyst,
            },
            {
                "title": "AWS Trainium 2 vs NVIDIA H100 Cost Analysis",
                "body_markdown": (
                    "# AWS Trainium 2 vs NVIDIA H100 Cost Analysis\n\n"
                    "## Motivation\n\n"
                    "Amazon has invested heavily in custom silicon to reduce dependency on NVIDIA "
                    "and offer customers a more cost-effective training option.\n\n"
                    "## Pricing Comparison\n\n"
                    "| Instance | GPU/Chip | On-Demand/hr | Spot/hr |\n"
                    "|----------|----------|--------------|----------|\n"
                    "| p4d.24xlarge | H100 (8x) | $32.77 | ~$10 |\n"
                    "| trn2.48xlarge | Trainium 2 (16x) | $21.50 (est) | ~$7 |\n\n"
                    "## Performance Notes\n\n"
                    "- Trainium 2 shows competitive performance on Llama and Mistral models\n"
                    "- Amazon internal benchmarks show 4x improvement over Trainium 1\n"
                    "- Limited third-party validation available\n\n"
                    "## Recommendation\n\n"
                    "Trainium 2 is worth evaluating for pure AWS workloads. Mixed cloud "
                    "shops should stick with H100/H200 for portability."
                ),
                "status": NoteStatus.draft,
                "tags": ["aws", "training", "cost-analysis", "custom-silicon"],
                "links": [
                    (EntityType.hardware_product, hw_trainium2),
                    (EntityType.company, co_amazon),
                ],
                "author": analyst,
            },
            {
                "title": "Meta AI Infrastructure Strategy",
                "body_markdown": (
                    "# Meta AI Infrastructure Strategy\n\n"
                    "## Overview\n\n"
                    "Meta is one of the largest consumers of AI compute globally, "
                    "operating massive GPU clusters for Llama model training and "
                    "recommendation system inference.\n\n"
                    "## Scale\n\n"
                    "- 350,000+ H100 GPUs as of Q1 2025\n"
                    "- $60–65B CapEx planned for 2025\n"
                    "- Texas campus at 800MW capacity\n\n"
                    "## Open Source Strategy\n\n"
                    "Meta's open-source Llama models create ecosystem leverage and reduce "
                    "NVIDIA's per-unit pricing power over Meta specifically.\n\n"
                    "## Custom Silicon\n\n"
                    "Meta MTIA (Meta Training and Inference Accelerator) chips are being "
                    "deployed for recommendation models, reducing GPU dependency for that workload."
                ),
                "status": NoteStatus.review,
                "tags": ["meta", "cloud", "strategy", "llm"],
                "links": [
                    (EntityType.company, co_meta),
                    (EntityType.datacenter, dc_meta),
                ],
                "author": analyst,
            },
        ]

        for nd in note_data:
            existing_note = await _get_or_skip(session, ResearchNote, title=nd["title"])
            if existing_note:
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
                author_id=nd["author"].id,
                published_at=now if nd["status"] == NoteStatus.published else None,
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
        def _monthly_ts(year: int, month: int) -> datetime.datetime:
            return datetime.datetime(year, month, 1, tzinfo=datetime.timezone.utc)

        months = []
        for i in range(18):
            y, m = divmod(2024 * 12 + i, 12)
            months.append(_monthly_ts(y, m + 1))

        metric_series_data = []

        # Re-fetch IDs (they may have just been created)
        hw_h100 = await _get_or_skip(session, HardwareProduct, name="H100", vendor="NVIDIA")
        hw_mi300x = await _get_or_skip(session, HardwareProduct, name="MI300X", vendor="AMD")
        co_nvidia = await _get_or_skip(session, Company, name="NVIDIA")
        co_amd = await _get_or_skip(session, Company, name="AMD")
        co_intel = await _get_or_skip(session, Company, name="Intel")
        co_microsoft = await _get_or_skip(session, Company, name="Microsoft")
        dc_us = await _get_or_skip(session, DatacenterSite, name="US West GPU Cluster")
        dc_eu = await _get_or_skip(session, DatacenterSite, name="EU AI Datacenter")
        dc_azure = await _get_or_skip(session, DatacenterSite, name="Azure East US AI Hub")
        dc_coreweave = await _get_or_skip(session, DatacenterSite, name="CoreWeave Chicago")
        dc_meta = await _get_or_skip(session, DatacenterSite, name="Meta AI Texas Campus")

        if hw_h100:
            metric_series_data.append({
                "name": "H100 Shipment Volume",
                "entity_type": MetricEntityType.hardware_product,
                "entity_id": hw_h100.id,
                "unit": "units (thousands)",
                "frequency": MetricFrequency.monthly,
                "source": "Industry estimates",
                "values": [12, 15, 18, 22, 28, 35, 42, 50, 58, 65, 70, 74, 78, 80, 82, 83, 84, 85],
            })

        if hw_mi300x:
            metric_series_data.append({
                "name": "MI300X Shipment Volume",
                "entity_type": MetricEntityType.hardware_product,
                "entity_id": hw_mi300x.id,
                "unit": "units (thousands)",
                "frequency": MetricFrequency.monthly,
                "source": "Industry estimates",
                "values": [0, 1, 2, 4, 6, 10, 14, 18, 23, 28, 32, 36, 40, 43, 46, 48, 50, 52],
            })

        if co_nvidia:
            metric_series_data.append({
                "name": "NVIDIA Revenue",
                "entity_type": MetricEntityType.company,
                "entity_id": co_nvidia.id,
                "unit": "USD billions",
                "frequency": MetricFrequency.monthly,
                "source": "Public filings (quarterly, annualized)",
                "values": [6.1, 7.2, 9.0, 10.3, 11.8, 13.5, 15.2, 17.8, 19.1, 20.4, 22.1, 23.5, 24.9, 26.0, 27.2, 28.5, 29.0, 29.8],
            })

        if co_amd:
            metric_series_data.append({
                "name": "AMD Data Center Revenue",
                "entity_type": MetricEntityType.company,
                "entity_id": co_amd.id,
                "unit": "USD billions",
                "frequency": MetricFrequency.monthly,
                "source": "Public filings",
                "values": [0.4, 0.5, 0.6, 0.9, 1.2, 1.6, 2.1, 2.6, 3.0, 3.3, 3.7, 4.0, 4.3, 4.5, 4.7, 4.9, 5.1, 5.3],
            })

        if co_intel:
            metric_series_data.append({
                "name": "Intel Data Center & AI Revenue",
                "entity_type": MetricEntityType.company,
                "entity_id": co_intel.id,
                "unit": "USD billions",
                "frequency": MetricFrequency.monthly,
                "source": "Public filings",
                "values": [2.8, 2.6, 2.5, 2.4, 2.3, 2.5, 2.7, 2.8, 2.9, 3.0, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8],
            })

        if co_microsoft:
            metric_series_data.append({
                "name": "Microsoft Azure Revenue",
                "entity_type": MetricEntityType.company,
                "entity_id": co_microsoft.id,
                "unit": "USD billions",
                "frequency": MetricFrequency.monthly,
                "source": "Public filings",
                "values": [7.1, 7.5, 8.0, 8.5, 9.0, 9.6, 10.2, 10.8, 11.5, 12.1, 12.8, 13.5, 14.2, 14.9, 15.6, 16.3, 17.0, 17.8],
            })

        if dc_us:
            metric_series_data.append({
                "name": "US West DC Power Usage",
                "entity_type": MetricEntityType.datacenter,
                "entity_id": dc_us.id,
                "unit": "MW",
                "frequency": MetricFrequency.monthly,
                "source": "Internal telemetry",
                "values": [320, 335, 348, 362, 378, 390, 405, 420, 434, 445, 455, 462, 468, 472, 476, 479, 481, 483],
            })

        if dc_eu:
            metric_series_data.append({
                "name": "EU AI DC Power Usage",
                "entity_type": MetricEntityType.datacenter,
                "entity_id": dc_eu.id,
                "unit": "MW",
                "frequency": MetricFrequency.monthly,
                "source": "Internal telemetry",
                "values": [180, 188, 195, 202, 210, 217, 224, 230, 237, 243, 248, 252, 256, 259, 261, 263, 265, 267],
            })

        if dc_azure:
            metric_series_data.append({
                "name": "Azure East US Power Usage",
                "entity_type": MetricEntityType.datacenter,
                "entity_id": dc_azure.id,
                "unit": "MW",
                "frequency": MetricFrequency.monthly,
                "source": "Internal telemetry",
                "values": [380, 400, 425, 450, 480, 510, 535, 560, 585, 605, 620, 635, 642, 648, 651, 648, 649, 650],
            })

        if dc_coreweave:
            metric_series_data.append({
                "name": "CoreWeave Chicago Power Usage",
                "entity_type": MetricEntityType.datacenter,
                "entity_id": dc_coreweave.id,
                "unit": "MW",
                "frequency": MetricFrequency.monthly,
                "source": "Internal telemetry",
                "values": [40, 55, 70, 85, 100, 115, 128, 138, 148, 155, 160, 165, 168, 171, 173, 175, 177, 178],
            })

        if dc_meta:
            metric_series_data.append({
                "name": "Meta Texas Campus Power Usage",
                "entity_type": MetricEntityType.datacenter,
                "entity_id": dc_meta.id,
                "unit": "MW",
                "frequency": MetricFrequency.monthly,
                "source": "Internal telemetry",
                "values": [200, 240, 290, 340, 400, 460, 520, 570, 610, 650, 685, 710, 730, 748, 761, 771, 778, 783],
            })

        for ms_data in metric_series_data:
            existing_series = await _get_or_skip(
                session, MetricSeries,
                name=ms_data["name"],
                entity_id=ms_data["entity_id"],
            )
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
            logger.info("Created MetricSeries '%s' with %d points.", ms_data["name"], len(rows))

        await session.commit()

        # ── Source Documents (simulated ingestion results) ─────────────────────
        def _content_hash(title: str, url: str | None, published_at: datetime.datetime | None, raw_text: str) -> str:
            pub_str = published_at.isoformat() if published_at else ""
            raw = f"{title}|{url or ''}|{pub_str}|{raw_text[:500]}"
            return hashlib.sha256(raw.encode()).hexdigest()

        # Re-fetch entity IDs for source entity links
        co_nvidia = await _get_or_skip(session, Company, name="NVIDIA")
        co_amd = await _get_or_skip(session, Company, name="AMD")
        co_intel = await _get_or_skip(session, Company, name="Intel")
        co_google = await _get_or_skip(session, Company, name="Google")
        co_microsoft = await _get_or_skip(session, Company, name="Microsoft")
        co_meta = await _get_or_skip(session, Company, name="Meta")
        co_tsmc = await _get_or_skip(session, Company, name="TSMC")
        hw_h100 = await _get_or_skip(session, HardwareProduct, name="H100", vendor="NVIDIA")
        hw_h200 = await _get_or_skip(session, HardwareProduct, name="H200", vendor="NVIDIA")
        hw_b100 = await _get_or_skip(session, HardwareProduct, name="B100", vendor="NVIDIA")
        hw_mi300x = await _get_or_skip(session, HardwareProduct, name="MI300X", vendor="AMD")
        hw_gaudi3 = await _get_or_skip(session, HardwareProduct, name="Gaudi 3", vendor="Intel")
        dc_us = await _get_or_skip(session, DatacenterSite, name="US West GPU Cluster")
        dc_meta = await _get_or_skip(session, DatacenterSite, name="Meta AI Texas Campus")
        dc_azure = await _get_or_skip(session, DatacenterSite, name="Azure East US AI Hub")

        source_docs = [
            {
                "title": "NVIDIA Reports Record Q4 FY2025 Revenue of $39.3 Billion",
                "url": "https://investor.nvidia.com/news-details/2025/NVIDIA-Reports-Record-Revenue",
                "publisher": "NVIDIA Investor Relations",
                "published_at": datetime.datetime(2025, 2, 26, 17, 0, tzinfo=datetime.timezone.utc),
                "raw_text": (
                    "NVIDIA today reported revenue for the fourth quarter ended January 26, 2025, of $39.3 billion, "
                    "up 12% from the previous quarter and up 78% from a year ago. GAAP earnings per diluted share "
                    "for the quarter were $0.89, up 14% from the previous quarter and up 82% from a year ago. "
                    "Data Center quarterly revenue was $35.6 billion, up 16% from the previous quarter and up 93% "
                    "from a year ago, driven by strong demand for Hopper and Blackwell GPU computing platforms. "
                    "CEO Jensen Huang said: 'The age of AI is full on. Physical AI and agentic AI are driving "
                    "a new wave of investment in AI infrastructure worldwide.'"
                ),
                "source_type": SourceType.json,
                "source_name": "nvidia_press_releases",
                "extracted_entities": {"companies": [{"id": str(co_nvidia.id) if co_nvidia else None, "name": "NVIDIA"}]},
                "entity_links": [("company", co_nvidia, "NVIDIA")],
            },
            {
                "title": "AMD MI300X Achieves 60% Market Share in Hyperscaler Inference Deployments",
                "url": "https://www.semianalysis.com/p/amd-mi300x-market-share",
                "publisher": "SemiAnalysis",
                "published_at": datetime.datetime(2025, 1, 15, 9, 0, tzinfo=datetime.timezone.utc),
                "raw_text": (
                    "AMD's MI300X accelerator has captured approximately 60% of new hyperscaler inference "
                    "deployments outside of NVIDIA's core enterprise customer base, according to SemiAnalysis "
                    "research. The chip's 192GB HBM3 memory capacity gives it a decisive advantage for serving "
                    "large language models with long context windows. Microsoft Azure has deployed MI300X in its "
                    "ND MI300X v5 series, and Meta is evaluating the chip for its recommendation engine "
                    "inference workloads. AMD reported data center revenue of $2.3 billion in Q3 2024, "
                    "primarily driven by MI300X shipments."
                ),
                "source_type": SourceType.json,
                "source_name": "semianalysis_reports",
                "extracted_entities": {
                    "companies": [{"id": str(co_amd.id) if co_amd else None, "name": "AMD"}],
                    "hardware_products": [{"id": str(hw_mi300x.id) if hw_mi300x else None, "name": "MI300X"}],
                },
                "entity_links": [
                    ("company", co_amd, "AMD"),
                    ("hardware_product", hw_mi300x, "MI300X"),
                ],
            },
            {
                "title": "TSMC CoWoS Capacity to Triple by Q4 2025 Amid AI Chip Demand",
                "url": "https://www.digitimes.com/news/tsmc-cowos-capacity-expansion",
                "publisher": "DigiTimes",
                "published_at": datetime.datetime(2024, 11, 20, 8, 0, tzinfo=datetime.timezone.utc),
                "raw_text": (
                    "TSMC is on track to triple its CoWoS advanced packaging capacity by the end of 2025, "
                    "according to supply chain sources. The expansion is driven by insatiable demand for "
                    "NVIDIA's H100, H200, and upcoming Blackwell B100 GPUs, as well as AMD's MI300X and "
                    "Apple's M-series chips. Current CoWoS capacity stands at approximately 35,000 wafers "
                    "per month, with the target of reaching 100,000 wafers per month. "
                    "Capital expenditure for packaging alone is estimated at $10 billion through 2026."
                ),
                "source_type": SourceType.rss,
                "source_name": "digitimes_rss",
                "extracted_entities": {
                    "companies": [{"id": str(co_tsmc.id) if co_tsmc else None, "name": "TSMC"}],
                    "hardware_products": [
                        {"id": str(hw_h100.id) if hw_h100 else None, "name": "H100"},
                        {"id": str(hw_b100.id) if hw_b100 else None, "name": "B100"},
                    ],
                },
                "entity_links": [
                    ("company", co_tsmc, "TSMC"),
                    ("hardware_product", hw_h100, "H100"),
                ],
            },
            {
                "title": "Microsoft Commits $80 Billion to AI Data Centers in 2025",
                "url": "https://blogs.microsoft.com/blog/2025/01/microsoft-ai-infrastructure-2025",
                "publisher": "Microsoft Official Blog",
                "published_at": datetime.datetime(2025, 1, 3, 12, 0, tzinfo=datetime.timezone.utc),
                "raw_text": (
                    "Microsoft plans to invest $80 billion in AI-enabled data center infrastructure "
                    "in fiscal year 2025, with more than half of this investment going to the United States. "
                    "This investment will enable Microsoft to train large AI models and deploy AI and cloud-based "
                    "applications around the world. The investment reflects the extraordinary demand for AI "
                    "compute and the confidence Microsoft has in the transformative potential of AI. "
                    "Microsoft's Azure has become the go-to platform for OpenAI workloads and is expanding "
                    "its fleet of H100 and Blackwell GPU clusters."
                ),
                "source_type": SourceType.rss,
                "source_name": "microsoft_blog_rss",
                "extracted_entities": {
                    "companies": [{"id": str(co_microsoft.id) if co_microsoft else None, "name": "Microsoft"}],
                },
                "entity_links": [
                    ("company", co_microsoft, "Microsoft"),
                    ("datacenter", dc_azure, "Azure East US AI Hub"),
                ],
            },
            {
                "title": "Google DeepMind Publishes Gemini 2.0 Training Details on TPU v5p",
                "url": "https://deepmind.google/research/gemini-2-technical-report",
                "publisher": "Google DeepMind",
                "published_at": datetime.datetime(2025, 3, 1, 10, 0, tzinfo=datetime.timezone.utc),
                "raw_text": (
                    "Google DeepMind has published details on how Gemini 2.0 was trained using a fleet of "
                    "TPU v5p pods across Google's global data center network. The training run used over "
                    "50,000 TPU v5p chips interconnected via Google's custom ICI (Inter-Chip Interconnect) "
                    "fabric at 4800 Gb/s per chip. The model achieved state-of-the-art results on MMLU, "
                    "HumanEval, and MATH benchmarks. Google claims TPU v5p offers 60% better price-performance "
                    "than H100 for JAX-based transformer training workloads."
                ),
                "source_type": SourceType.json,
                "source_name": "deepmind_research",
                "extracted_entities": {
                    "companies": [{"id": str(co_google.id) if co_google else None, "name": "Google"}],
                },
                "entity_links": [("company", co_google, "Google")],
            },
            {
                "title": "NVIDIA Blackwell B100 Production Yield Issues Delay Volume Shipments",
                "url": "https://www.theinformation.com/articles/nvidia-blackwell-yield-issues",
                "publisher": "The Information",
                "published_at": datetime.datetime(2024, 8, 5, 14, 30, tzinfo=datetime.timezone.utc),
                "raw_text": (
                    "NVIDIA's Blackwell B100 GPUs have experienced significant production yield issues at TSMC "
                    "that have pushed back volume shipments by approximately two quarters, according to sources "
                    "familiar with the matter. The yield problems relate to the chip's 3nm process node and "
                    "the complex multi-die design. NVIDIA has reportedly redesigned the packaging to address "
                    "the issues, and volume production is now expected in Q1 2025 rather than Q3 2024. "
                    "Hyperscalers including Amazon, Microsoft, and Google have been informed of the delay."
                ),
                "source_type": SourceType.json,
                "source_name": "theinformation_articles",
                "extracted_entities": {
                    "companies": [{"id": str(co_nvidia.id) if co_nvidia else None, "name": "NVIDIA"}],
                    "hardware_products": [{"id": str(hw_b100.id) if hw_b100 else None, "name": "B100"}],
                },
                "entity_links": [
                    ("company", co_nvidia, "NVIDIA"),
                    ("hardware_product", hw_b100, "B100"),
                ],
            },
            {
                "title": "Intel Gaudi 3 Benchmarks Show Competitive LLM Inference Performance",
                "url": "https://www.intel.com/content/www/us/en/developer/articles/technical/gaudi3-llm-benchmarks",
                "publisher": "Intel Developer Zone",
                "published_at": datetime.datetime(2024, 9, 18, 9, 0, tzinfo=datetime.timezone.utc),
                "raw_text": (
                    "Intel has published detailed benchmark results for Gaudi 3 across a range of LLM inference "
                    "workloads. On Llama 3 70B with FP8 precision, Gaudi 3 achieves 1,847 tokens/second compared "
                    "to H100's 1,256 tokens/second — a 47% performance advantage. For Mixtral 8x7B inference, "
                    "Gaudi 3 delivers 3,100 tokens/second. Intel attributes the gains to Gaudi 3's 3.7 TB/s "
                    "memory bandwidth and optimized attention kernels in the SynapseAI software stack. "
                    "Gaudi 3 is available on Intel Tiber AI Cloud and through major OEM partners."
                ),
                "source_type": SourceType.json,
                "source_name": "intel_developer_articles",
                "extracted_entities": {
                    "companies": [{"id": str(co_intel.id) if co_intel else None, "name": "Intel"}],
                    "hardware_products": [{"id": str(hw_gaudi3.id) if hw_gaudi3 else None, "name": "Gaudi 3"}],
                },
                "entity_links": [
                    ("company", co_intel, "Intel"),
                    ("hardware_product", hw_gaudi3, "Gaudi 3"),
                ],
            },
            {
                "title": "Meta Orders 350,000 H100 GPUs for Llama 4 Training",
                "url": "https://www.wsj.com/tech/ai/meta-350000-nvidia-h100-gpus",
                "publisher": "Wall Street Journal",
                "published_at": datetime.datetime(2024, 10, 22, 16, 0, tzinfo=datetime.timezone.utc),
                "raw_text": (
                    "Meta Platforms has placed orders for approximately 350,000 NVIDIA H100 GPUs to support "
                    "training of its next-generation Llama 4 family of large language models, according to "
                    "people familiar with the matter. The order, worth an estimated $10 billion, represents "
                    "one of the single largest GPU purchases in history. The chips will be deployed across "
                    "Meta's Texas and Louisiana data center campuses, which are being expanded to accommodate "
                    "the massive power requirements. Meta CEO Mark Zuckerberg has made AI the company's top "
                    "investment priority for 2025 and 2026."
                ),
                "source_type": SourceType.rss,
                "source_name": "wsj_tech_rss",
                "extracted_entities": {
                    "companies": [
                        {"id": str(co_meta.id) if co_meta else None, "name": "Meta"},
                        {"id": str(co_nvidia.id) if co_nvidia else None, "name": "NVIDIA"},
                    ],
                    "hardware_products": [{"id": str(hw_h100.id) if hw_h100 else None, "name": "H100"}],
                },
                "entity_links": [
                    ("company", co_meta, "Meta"),
                    ("hardware_product", hw_h100, "H100"),
                    ("datacenter", dc_meta, "Meta AI Texas Campus"),
                ],
            },
            {
                "title": "H200 SXM Availability Expands to All Major Cloud Providers",
                "url": "https://nvidianews.nvidia.com/news/h200-cloud-availability",
                "publisher": "NVIDIA Newsroom",
                "published_at": datetime.datetime(2024, 5, 21, 13, 0, tzinfo=datetime.timezone.utc),
                "raw_text": (
                    "NVIDIA today announced that H200 SXM GPU instances are now available through Amazon Web "
                    "Services, Google Cloud Platform, Microsoft Azure, and Oracle Cloud Infrastructure. "
                    "The H200 features 141GB of HBM3e memory — nearly double the bandwidth of HBM3 — enabling "
                    "significantly faster inference for large language models with long context windows. "
                    "Early benchmarks show H200 delivers 1.4x the tokens-per-second of H100 on Llama 3 70B. "
                    "Cloud pricing starts at $5.96/hour on AWS for a single H200."
                ),
                "source_type": SourceType.json,
                "source_name": "nvidia_newsroom",
                "extracted_entities": {
                    "companies": [{"id": str(co_nvidia.id) if co_nvidia else None, "name": "NVIDIA"}],
                    "hardware_products": [{"id": str(hw_h200.id) if hw_h200 else None, "name": "H200"}],
                },
                "entity_links": [
                    ("company", co_nvidia, "NVIDIA"),
                    ("hardware_product", hw_h200, "H200"),
                ],
            },
            {
                "title": "US West GPU Cluster Reaches 87% Utilization, Expansion Planned",
                "url": None,
                "publisher": "Internal Operations Report",
                "published_at": datetime.datetime(2026, 1, 15, 0, 0, tzinfo=datetime.timezone.utc),
                "raw_text": (
                    "The US West GPU Cluster has reached 87% average utilization across all H100 nodes "
                    "as of Q1 2026. Peak utilization during LLM training jobs reaches 98%. "
                    "Power draw is averaging 483 MW, approaching the facility's 500 MW capacity limit. "
                    "Operations team recommends initiating Phase 2 expansion planning immediately. "
                    "Estimated cost for 200 MW additional capacity is $400M including cooling upgrades."
                ),
                "source_type": SourceType.file,
                "source_name": "internal_ops_reports",
                "extracted_entities": {
                    "datacenters": [{"id": str(dc_us.id) if dc_us else None, "name": "US West GPU Cluster"}],
                    "hardware_products": [{"id": str(hw_h100.id) if hw_h100 else None, "name": "H100"}],
                },
                "entity_links": [
                    ("datacenter", dc_us, "US West GPU Cluster"),
                ],
            },
        ]

        # Create a seed ingestion run to associate with the documents
        seed_run = await _get_or_skip(session, IngestionRun, source_name="seed_initial")
        if not seed_run:
            seed_run = IngestionRun(
                id=uuid.uuid4(),
                triggered_by=None,
                source_type=SourceType.json,
                source_name="seed_initial",
                status=RunStatus.success,
                dry_run=False,
                finished_at=now,
                stats={"total": len(source_docs), "ingested": len(source_docs), "skipped": 0, "errors": 0},
            )
            session.add(seed_run)
            await session.flush()
            logger.info("Created seed ingestion run.")

        for sd in source_docs:
            content_hash = _content_hash(
                sd["title"], sd["url"], sd["published_at"], sd["raw_text"]
            )
            existing_doc = await _get_or_skip(session, SourceDocument, content_hash=content_hash)
            if existing_doc:
                logger.info("SourceDocument '%s' already exists, skipping.", sd["title"][:60])
                continue

            doc = SourceDocument(
                id=uuid.uuid4(),
                title=sd["title"],
                url=sd["url"],
                publisher=sd["publisher"],
                published_at=sd["published_at"],
                raw_text=sd["raw_text"],
                content_hash=content_hash,
                extracted_entities=sd["extracted_entities"],
                source_type=sd["source_type"],
                source_name=sd["source_name"],
                status=IngestionStatus.ingested,
            )
            session.add(doc)
            await session.flush()

            for entity_type, entity, entity_name in sd["entity_links"]:
                if entity is not None:
                    session.add(
                        SourceEntityLink(
                            id=uuid.uuid4(),
                            source_document_id=doc.id,
                            entity_type=entity_type,
                            entity_id=entity.id,
                            entity_name=entity_name,
                        )
                    )

            logger.info("Created source document: '%s'", sd["title"][:60])

        await session.commit()
        logger.info("Seed complete.")


if __name__ == "__main__":
    logging.basicConfig(level="INFO")
    asyncio.run(seed())
