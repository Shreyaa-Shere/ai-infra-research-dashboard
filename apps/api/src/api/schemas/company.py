import uuid
from datetime import datetime

from pydantic import BaseModel

from api.models.company import CompanyType


class CompanyCreate(BaseModel):
    name: str
    type: CompanyType
    region: str
    website: str | None = None


class CompanyUpdate(BaseModel):
    name: str | None = None
    type: CompanyType | None = None
    region: str | None = None
    website: str | None = None


class CompanyResponse(BaseModel):
    id: uuid.UUID
    name: str
    type: CompanyType
    region: str
    website: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
