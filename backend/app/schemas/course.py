"""
Course Schemas - Course, CurriculumMatrix, Subject, MatrixSubject
"""
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


# --- Subject ---
class SubjectCreate(BaseModel):
    course_id: Optional[UUID] = None
    name: str
    code: str
    workload_hours: int = 40
    description: Optional[str] = None


class SubjectUpdate(BaseModel):
    course_id: Optional[UUID] = None
    name: Optional[str] = None
    code: Optional[str] = None
    workload_hours: Optional[int] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class SubjectResponse(BaseModel):
    id: UUID
    course_id: Optional[UUID] = None
    name: str
    code: str
    workload_hours: int
    description: Optional[str] = None
    tenant_id: UUID
    is_active: bool
    created_at: datetime
    course_name: Optional[str] = None

    class Config:
        from_attributes = True


# --- Course ---
class CourseCreate(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    duration_semesters: int = 1


class CourseUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    duration_semesters: Optional[int] = None
    is_active: Optional[bool] = None


class CourseResponse(BaseModel):
    id: UUID
    name: str
    code: str
    description: Optional[str] = None
    duration_semesters: int
    tenant_id: UUID
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# --- CurriculumMatrix ---
class MatrixCreate(BaseModel):
    course_id: UUID
    name: str
    year: int


class MatrixUpdate(BaseModel):
    name: Optional[str] = None
    year: Optional[int] = None
    is_active: Optional[bool] = None


class MatrixResponse(BaseModel):
    id: UUID
    course_id: UUID
    name: str
    year: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# --- MatrixSubject ---
class MatrixSubjectCreate(BaseModel):
    matrix_id: UUID
    subject_id: UUID
    professor_id: Optional[UUID] = None
    semester: int = 1


class MatrixSubjectUpdate(BaseModel):
    professor_id: Optional[UUID] = None
    semester: Optional[int] = None
    is_active: Optional[bool] = None


class MatrixSubjectResponse(BaseModel):
    id: UUID
    matrix_id: UUID
    subject_id: UUID
    professor_id: Optional[UUID] = None
    semester: int
    is_active: bool
    subject_name: Optional[str] = None
    subject_code: Optional[str] = None
    workload_hours: Optional[int] = None

    class Config:
        from_attributes = True
