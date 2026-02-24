"""
Content Schemas - LessonPlan, Material, Announcement
"""
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


# --- LessonPlan ---
class LessonPlanCreate(BaseModel):
    matrix_subject_id: UUID
    date: datetime
    topic: str
    class_orders: Optional[list[int]] = []
    content: Optional[str] = None
    objectives: Optional[str] = None


class LessonPlanUpdate(BaseModel):
    date: Optional[datetime] = None
    topic: Optional[str] = None
    content: Optional[str] = None
    objectives: Optional[str] = None


class LessonPlanResponse(BaseModel):
    id: UUID
    matrix_subject_id: UUID
    professor_id: UUID
    date: datetime
    class_orders: Optional[list[int]] = []
    topic: str
    content: Optional[str] = None
    objectives: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# --- Material ---
class MaterialCreate(BaseModel):
    matrix_subject_id: UUID
    title: str
    description: Optional[str] = None
    file_url: Optional[str] = None
    file_type: Optional[str] = None


class MaterialResponse(BaseModel):
    id: UUID
    matrix_subject_id: UUID
    professor_id: UUID
    title: str
    description: Optional[str] = None
    file_url: Optional[str] = None
    file_type: Optional[str] = None
    file_size: Optional[str] = None
    uploaded_at: datetime

    class Config:
        from_attributes = True


# --- Announcement ---
class AnnouncementCreate(BaseModel):
    title: str
    content: str
    target: str = "all"  # all, course, subject
    target_id: Optional[UUID] = None
    pinned: bool = False
    expires_at: Optional[datetime] = None


class AnnouncementUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    target: Optional[str] = None
    target_id: Optional[UUID] = None
    pinned: Optional[bool] = None
    is_active: Optional[bool] = None
    expires_at: Optional[datetime] = None


class AnnouncementResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    author_id: UUID
    title: str
    content: str
    target: str
    target_id: Optional[UUID] = None
    pinned: bool
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True
