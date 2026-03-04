import uuid
from datetime import date, datetime

from pydantic import BaseModel

from api.models.hardware_product import HardwareCategory


class HardwareProductCreate(BaseModel):
    name: str
    vendor: str
    category: HardwareCategory
    release_date: date | None = None
    memory_gb: int | None = None
    tdp_watts: int | None = None
    process_node: str | None = None
    notes: str | None = None


class HardwareProductUpdate(BaseModel):
    name: str | None = None
    vendor: str | None = None
    category: HardwareCategory | None = None
    release_date: date | None = None
    memory_gb: int | None = None
    tdp_watts: int | None = None
    process_node: str | None = None
    notes: str | None = None


class HardwareProductResponse(BaseModel):
    id: uuid.UUID
    name: str
    vendor: str
    category: HardwareCategory
    release_date: date | None
    memory_gb: int | None
    tdp_watts: int | None
    process_node: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
