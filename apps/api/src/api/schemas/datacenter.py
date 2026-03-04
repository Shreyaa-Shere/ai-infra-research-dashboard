import uuid
from datetime import datetime

from pydantic import BaseModel

from api.models.datacenter_site import DatacenterStatus
from api.schemas.company import CompanyResponse


class DatacenterCreate(BaseModel):
    name: str
    region: str
    owner_company_id: uuid.UUID | None = None
    power_mw: int | None = None
    status: DatacenterStatus = DatacenterStatus.planned
    notes: str | None = None


class DatacenterUpdate(BaseModel):
    name: str | None = None
    region: str | None = None
    owner_company_id: uuid.UUID | None = None
    power_mw: int | None = None
    status: DatacenterStatus | None = None
    notes: str | None = None


class DatacenterResponse(BaseModel):
    id: uuid.UUID
    name: str
    region: str
    owner_company_id: uuid.UUID | None
    owner_company: CompanyResponse | None = None
    power_mw: int | None
    status: DatacenterStatus
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
