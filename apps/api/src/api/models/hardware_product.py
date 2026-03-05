import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Integer, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from api.db.engine import Base


class HardwareCategory(str, enum.Enum):
    GPU = "GPU"
    CPU = "CPU"
    Networking = "Networking"
    Accelerator = "Accelerator"


class HardwareProduct(Base):
    __tablename__ = "hardware_products"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    vendor: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    category: Mapped[HardwareCategory] = mapped_column(
        SAEnum(HardwareCategory, name="hardware_category"), nullable=False, index=True
    )
    release_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    memory_gb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tdp_watts: Mapped[int | None] = mapped_column(Integer, nullable=True)
    process_node: Mapped[str | None] = mapped_column(String(64), nullable=True)
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
