"""
Academic Period Schemas - Pydantic models for validation and serialization
"""
from datetime import date, time, datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from uuid import UUID


# ============= Enums =============

class BreakTypeEnum(str):
    MONTHLY = "mensal"
    BIMONTHLY = "bimestral"
    QUARTERLY = "trimestral"
    FOURMONTHLY = "quadrimestral"
    SEMIANNUAL = "semestral"
    ANNUAL = "anual"


class NonSchoolDayReasonEnum(str):
    SATURDAY = "sabado"
    SUNDAY = "domingo"
    HOLIDAY = "feriado"
    EVENT = "evento"
    OTHER = "outro"


# ============= PeriodBreak Schemas =============

class PeriodBreakBase(BaseModel):
    order: int = Field(..., description="Order number (1st, 2nd, etc)")
    name: str = Field(..., max_length=100, description="Break name (e.g., '1º Bimestre')")
    start_date: date
    end_date: date


class PeriodBreakCreate(PeriodBreakBase):
    pass


class PeriodBreakUpdate(BaseModel):
    order: Optional[int] = None
    name: Optional[str] = Field(None, max_length=100)
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class PeriodBreakResponse(PeriodBreakBase):
    id: UUID
    academic_period_id: UUID

    class Config:
        from_attributes = True


# ============= NonSchoolDay Schemas =============

class NonSchoolDayBase(BaseModel):
    date: date
    reason: str = Field(..., description="Reason: sabado, domingo, feriado, evento, outro")
    description: Optional[str] = Field(None, max_length=255)


class NonSchoolDayCreate(NonSchoolDayBase):
    pass


class NonSchoolDayResponse(NonSchoolDayBase):
    id: UUID
    academic_period_id: UUID

    class Config:
        from_attributes = True


# ============= ClassSchedule Schemas =============

class ClassScheduleBase(BaseModel):
    order: int = Field(..., description="Class order (1st, 2nd, etc)")
    start_time: time
    end_time: time


class ClassScheduleCreate(ClassScheduleBase):
    pass


class ClassScheduleUpdate(BaseModel):
    order: Optional[int] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None


class ClassScheduleResponse(ClassScheduleBase):
    id: UUID
    academic_period_id: UUID
    duration_minutes: Optional[int] = None

    class Config:
        from_attributes = True


# ============= AcademicPeriod Schemas =============

class AcademicPeriodBase(BaseModel):
    name: str = Field(..., max_length=255, description="Period name (e.g., 'Período 2026.1')")
    year: int = Field(..., ge=2000, le=2100)
    break_type: str = Field(..., description="mensal, bimestral, trimestral, quadrimestral, semestral, anual")
    start_date: date
    end_date: date
    classes_per_day: int = Field(default=1, ge=1, description="Number of classes per day")
    is_active: bool = True


class AcademicPeriodCreate(AcademicPeriodBase):
    pass


class AcademicPeriodUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    year: Optional[int] = Field(None, ge=2000, le=2100)
    break_type: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    classes_per_day: Optional[int] = Field(None, ge=1)
    is_active: Optional[bool] = None


class AcademicPeriodResponse(AcademicPeriodBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    period_breaks: List[PeriodBreakResponse] = []
    non_school_days: List[NonSchoolDayResponse] = []
    class_schedules: List[ClassScheduleResponse] = []
    extra_school_days: List["ExtraSchoolDayResponse"] = []

    class Config:
        from_attributes = True


# ============= ExtraSchoolDay Schemas =============

class ExtraSchoolDayBase(BaseModel):
    date: date
    description: Optional[str] = Field(None, max_length=255)


class ExtraSchoolDayCreate(ExtraSchoolDayBase):
    pass


class ExtraSchoolDayResponse(ExtraSchoolDayBase):
    id: UUID
    academic_period_id: UUID

    class Config:
        from_attributes = True


# ============= Statistics Schema =============

class PeriodStatistics(BaseModel):
    """Statistics calculated from the academic period"""
    period_id: UUID
    period_name: str
    total_days: int
    school_days: int  # Excluding weekends and non-school days
    non_school_days_count: int
    total_classes_available: int  # school_days * classes_per_day * schedules
    classes_per_day: int
    schedules_count: int
    breaks_count: int
    start_date: date
    end_date: date


# ============= Course Link Schema =============

class CourseLinkPeriod(BaseModel):
    """Link a course to an academic period"""
    academic_period_id: Optional[UUID] = Field(None, description="ID of the academic period, or null to unlink")
