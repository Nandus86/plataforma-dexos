"""
Assignment Schemas
"""
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class AssignmentCreate(BaseModel):
    matrix_subject_id: UUID
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    max_score: float = 10.0


class AssignmentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    max_score: Optional[float] = None
    is_active: Optional[bool] = None


class AssignmentResponse(BaseModel):
    id: UUID
    matrix_subject_id: UUID
    professor_id: UUID
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    max_score: float
    is_active: bool
    created_at: datetime
    submissions_count: int = 0

    class Config:
        from_attributes = True


class SubmissionCreate(BaseModel):
    assignment_id: UUID
    content: Optional[str] = None
    file_url: Optional[str] = None


class SubmissionGrade(BaseModel):
    score: float
    feedback: Optional[str] = None


class SubmissionResponse(BaseModel):
    id: UUID
    assignment_id: UUID
    student_id: UUID
    content: Optional[str] = None
    file_url: Optional[str] = None
    score: Optional[float] = None
    feedback: Optional[str] = None
    submitted_at: datetime
    graded_at: Optional[datetime] = None

    class Config:
        from_attributes = True
