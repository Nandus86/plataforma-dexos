from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class DeviceBase(BaseModel):
    name: str
    dev_index: str
    is_active: Optional[bool] = True


class DeviceCreate(DeviceBase):
    tenant_id: Optional[UUID] = None


class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None


class DeviceResponse(DeviceBase):
    id: UUID
    tenant_id: Optional[UUID]
    last_online: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True
