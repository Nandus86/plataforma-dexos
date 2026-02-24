"""
Class Group Schemas - ClassGroup (Turma), ClassGroupStudent, ClassGroupSubject, Grid
"""
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


# --- ClassGroup ---
class ClassGroupCreate(BaseModel):
    course_id: UUID
    academic_period_id: UUID
    period_break_id: Optional[UUID] = None
    name: str
    year: Optional[int] = None
    semester: Optional[int] = None
    shift: str = "noite"
    max_students: Optional[int] = None


class ClassGroupUpdate(BaseModel):
    academic_period_id: Optional[UUID] = None
    period_break_id: Optional[UUID] = None
    name: Optional[str] = None
    year: Optional[int] = None
    semester: Optional[int] = None
    shift: Optional[str] = None
    max_students: Optional[int] = None
    is_active: Optional[bool] = None


class ClassGroupResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    course_id: UUID
    academic_period_id: Optional[UUID] = None
    period_break_id: Optional[UUID] = None
    name: str
    year: int
    semester: Optional[int] = None
    shift: str
    max_students: Optional[int] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    academic_period_name: Optional[str] = None
    period_break_name: Optional[str] = None

    class Config:
        from_attributes = True


class ClassGroupDetailResponse(ClassGroupResponse):
    """Extended response with student count, subject count, and course name"""
    course_name: Optional[str] = None
    student_count: int = 0
    subject_count: int = 0


# --- ClassGroupStudent ---
class ClassGroupStudentCreate(BaseModel):
    enrollment_id: UUID


class ClassGroupStudentResponse(BaseModel):
    id: UUID
    class_group_id: UUID
    enrollment_id: UUID
    enrolled_at: datetime
    student_name: Optional[str] = None
    student_email: Optional[str] = None
    registration_number: Optional[str] = None

    class Config:
        from_attributes = True


# --- ClassGroupSubject ---
class ProfessorAssignmentCreate(BaseModel):
    professor_id: UUID
    assigned_hours: int = 0


class ClassGroupSubjectCreate(BaseModel):
    subject_id: UUID
    professors: list[ProfessorAssignmentCreate] = []


class ProfessorAssignmentResponse(BaseModel):
    professor_id: UUID
    professor_name: str
    assigned_hours: int

    class Config:
        from_attributes = True


class ClassGroupSubjectResponse(BaseModel):
    id: UUID
    class_group_id: UUID
    subject_id: UUID
    professors: list[ProfessorAssignmentResponse] = []
    subject_name: Optional[str] = None
    workload_hours: Optional[int] = None

    class Config:
        from_attributes = True


# --- Student-Subject Grid ---
class StudentSubjectStatusUpdate(BaseModel):
    is_active: bool
    reason: Optional[str] = None


class StudentSubjectStatusResponse(BaseModel):
    id: UUID
    class_group_id: UUID
    enrollment_id: UUID
    subject_id: UUID
    is_active: bool
    reason: Optional[str] = None
    student_name: Optional[str] = None
    subject_name: Optional[str] = None

    class Config:
        from_attributes = True
