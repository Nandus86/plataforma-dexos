"""
Occurrence Schemas
"""
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class OccurrenceCreate(BaseModel):
    student_id: UUID
    type: str  # praise, warning, complaint, observation
    title: str
    description: Optional[str] = None
    date: Optional[datetime] = None


class OccurrenceUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    parent_notified: Optional[bool] = None


class OccurrenceResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    student_id: UUID
    author_id: UUID
    type: str
    title: str
    description: Optional[str] = None
    date: datetime
    parent_notified: bool
    created_at: datetime

    class Config:
        from_attributes = True
