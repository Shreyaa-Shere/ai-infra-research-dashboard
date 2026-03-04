import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from api.db.engine import Base

if TYPE_CHECKING:
    from api.models.company import Company


class DatacenterStatus(str, enum.Enum):
    planned = "planned"
    active = "active"
    retired = "retired"


class DatacenterSite(Base):
    __tablename__ = "datacenter_sites"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    region: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    owner_company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    power_mw: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[DatacenterStatus] = mapped_column(
        SAEnum(DatacenterStatus, name="datacenter_status"),
        nullable=False,
        default=DatacenterStatus.planned,
        index=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    owner_company: Mapped["Company | None"] = relationship(
        "Company", back_populates="datacenter_sites"
    )
