import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from api.db.engine import Base

if TYPE_CHECKING:
    from api.models.datacenter_site import DatacenterSite


class CompanyType(str, enum.Enum):
    fab = "fab"
    idm = "idm"
    cloud = "cloud"
    vendor = "vendor"
    research = "research"


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    type: Mapped[CompanyType] = mapped_column(
        SAEnum(CompanyType, name="company_type"), nullable=False, index=True
    )
    region: Mapped[str] = mapped_column(String(128), nullable=False)
    website: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    datacenter_sites: Mapped[list["DatacenterSite"]] = relationship(
        "DatacenterSite", back_populates="owner_company"
    )
