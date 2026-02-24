"""
Tenant Schemas
"""
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class TenantCreate(BaseModel):
    name: str
    slug: str
    domain: Optional[str] = None
    settings_json: Optional[str] = None


class TenantUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    domain: Optional[str] = None
    is_active: Optional[bool] = None
    settings_json: Optional[str] = None


class TenantResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    domain: Optional[str] = None
    is_active: bool
    settings_json: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
