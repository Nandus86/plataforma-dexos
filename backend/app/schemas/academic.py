"""
Academic Schemas - Enrollment, Grade, Attendance
"""
from pydantic import BaseModel, field_validator
from typing import Optional
from uuid import UUID
from datetime import datetime


# --- Enrollment ---
class EnrollmentCreate(BaseModel):
    student_id: UUID
    course_id: UUID
    year: int
    academic_period_id: UUID
    period_break_ids: list[UUID]


class EnrollmentUpdate(BaseModel):
    status: Optional[str] = None


class PeriodBreakSimple(BaseModel):
    id: UUID
    name: str

    class Config:
        from_attributes = True


class EnrollmentResponse(BaseModel):
    id: UUID
    student_id: UUID
    course_id: UUID
    year: int
    academic_period_id: UUID
    period_breaks: list[PeriodBreakSimple] = []
    enrollment_code: Optional[str] = None
    status: str
    created_at: datetime
    student_name: Optional[str] = None
    course_name: Optional[str] = None
    academic_period_name: Optional[str] = None

    class Config:
        from_attributes = True


# --- Grade ---
class GradeCreate(BaseModel):
    enrollment_id: UUID
    lesson_plan_id: Optional[UUID] = None
    evaluation_name: str
    value: float
    max_value: float = 10.0
    date: Optional[datetime] = None
    observations: Optional[str] = None


class GradeUpdate(BaseModel):
    lesson_plan_id: Optional[UUID] = None
    evaluation_name: Optional[str] = None
    value: Optional[float] = None
    max_value: Optional[float] = None
    date: Optional[datetime] = None
    observations: Optional[str] = None


class GradeResponse(BaseModel):
    id: UUID
    enrollment_id: UUID
    lesson_plan_id: Optional[UUID] = None
    evaluation_name: str
    value: float
    max_value: float
    date: Optional[datetime] = None
    observations: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# --- Attendance ---
class AttendanceCreate(BaseModel):
    enrollment_id: UUID
    lesson_plan_id: Optional[UUID] = None
    class_order_item: Optional[int] = None
    class_date: datetime
    present: bool = False
    checkin_method: str = "manual"
    observation: Optional[str] = None

    @field_validator('class_date', mode='before')
    @classmethod
    def strip_timezone(cls, v):
        if isinstance(v, datetime) and v.tzinfo is not None:
            return v.replace(tzinfo=None)
        if isinstance(v, str):
            dt = datetime.fromisoformat(v.replace('Z', '+00:00'))
            return dt.replace(tzinfo=None)
        return v


class AttendanceBulkCreate(BaseModel):
    """Bulk attendance for a class session"""
    matrix_subject_id: UUID
    lesson_plan_id: Optional[UUID] = None
    class_order_item: Optional[int] = None
    class_date: datetime
    records: list["AttendanceRecord"]

    @field_validator('class_date', mode='before')
    @classmethod
    def strip_timezone(cls, v):
        if isinstance(v, datetime) and v.tzinfo is not None:
            return v.replace(tzinfo=None)
        if isinstance(v, str):
            dt = datetime.fromisoformat(v.replace('Z', '+00:00'))
            return dt.replace(tzinfo=None)
        return v


class AttendanceRecord(BaseModel):
    student_id: UUID
    present: bool
    observation: Optional[str] = None


class AttendanceCheckin(BaseModel):
    """API-based check-in for a student"""
    student_id: UUID
    matrix_subject_id: UUID
    checkin_method: str = "api"


class AttendanceBiometricCheckin(BaseModel):
    """Machine-to-Machine Checkin from Biometric Hardware"""
    registration_number: str
    checkin_method: str = "biometric"
    timestamp: Optional[datetime] = None  # To allow hardware to send delayed syncs


class AttendanceResponse(BaseModel):
    id: UUID
    enrollment_id: UUID
    lesson_plan_id: Optional[UUID] = None
    class_order_item: Optional[int] = None
    class_date: datetime
    present: bool
    checkin_method: str
    observation: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Rebuild for forward refs
AttendanceBulkCreate.model_rebuild()


# --- Boletim ---
class GradeSummary(BaseModel):
    id: UUID
    evaluation_name: str
    value: float
    max_value: float
    date: Optional[datetime] = None
    lesson_plan_id: Optional[UUID] = None
    observations: Optional[str] = None

class SubjectBoletim(BaseModel):
    subject_id: UUID
    subject_name: str
    total_planned_classes: int
    total_presences: int
    frequency_percentage: float
    grades: list[GradeSummary]

class BoletimResponse(BaseModel):
    student_id: UUID
    student_name: str
    enrollment_id: UUID
    course_id: UUID
    course_name: str
    academic_period_id: UUID
    academic_period_name: str
    subjects: list[SubjectBoletim]
