"""Rules-based entity extractor.

Loads all known entity names from the DB and matches them
case-insensitively against the document title + raw_text.
"""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class EntityExtractor:
    async def extract(
        self,
        session: AsyncSession,
        title: str,
        raw_text: str | None,
    ) -> dict:
        """Return extracted_entities dict with matched hardware/company/datacenter."""
        from api.models.company import Company
        from api.models.datacenter_site import DatacenterSite
        from api.models.hardware_product import HardwareProduct

        full_text = (title + " " + (raw_text or "")).lower()

        hw_rows = (await session.execute(select(HardwareProduct))).scalars().all()
        co_rows = (await session.execute(select(Company))).scalars().all()
        dc_rows = (await session.execute(select(DatacenterSite))).scalars().all()

        result: dict = {
            "hardware_products": [],
            "companies": [],
            "datacenters": [],
        }

        for hw in hw_rows:
            if hw.name.lower() in full_text:
                result["hardware_products"].append(
                    {"id": str(hw.id), "name": hw.name, "match": hw.name}
                )

        for co in co_rows:
            if co.name.lower() in full_text:
                result["companies"].append(
                    {"id": str(co.id), "name": co.name, "match": co.name}
                )

        for dc in dc_rows:
            if dc.name.lower() in full_text:
                result["datacenters"].append(
                    {"id": str(dc.id), "name": dc.name, "match": dc.name}
                )

        total = (
            len(result["hardware_products"])
            + len(result["companies"])
            + len(result["datacenters"])
        )
        logger.debug("Extracted %d entities from '%s'", total, title[:60])
        return result
