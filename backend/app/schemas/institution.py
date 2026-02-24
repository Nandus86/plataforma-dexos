"""
Institution Schemas
"""
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class InstitutionUpdate(BaseModel):
    name: Optional[str] = None
    cnpj: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    principal_name: Optional[str] = None
    address_street: Optional[str] = None
    address_number: Optional[str] = None
    address_complement: Optional[str] = None
    address_neighborhood: Optional[str] = None
    address_city: Optional[str] = None
    address_state: Optional[str] = None
    address_zip: Optional[str] = None


class InstitutionResponse(InstitutionUpdate):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
