from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime
from app.models.content import ActivityType

class LessonPlanCreate(BaseModel):
    matrix_subject_id: Optional[UUID] = None
    class_group_subject_id: Optional[UUID] = None
    date: datetime
    class_orders: list[int] = []
    topic: str
    content: Optional[str] = None
    objectives: Optional[str] = None
    description: Optional[str] = None
    activity_type: ActivityType = ActivityType.none
    other_activity_reason: Optional[str] = None
    max_score: Optional[float] = 10.0

class LessonPlanUpdate(BaseModel):
    date: Optional[datetime] = None
    class_orders: Optional[list[int]] = None
    topic: Optional[str] = None
    content: Optional[str] = None
    objectives: Optional[str] = None
    description: Optional[str] = None
    activity_type: Optional[ActivityType] = None
    other_activity_reason: Optional[str] = None
    max_score: Optional[float] = None

class LessonPlanResponse(BaseModel):
    id: UUID
    matrix_subject_id: UUID
    professor_id: UUID
    class_group_subject_id: Optional[UUID] = None
    date: datetime
    class_orders: Optional[list[int]] = []
    topic: str
    content: Optional[str] = None
    objectives: Optional[str] = None
    description: Optional[str] = None
    activity_type: ActivityType
    other_activity_reason: Optional[str] = None
    max_score: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Schemas for side-loaded data (Attendance/Grades generated)
class AttendanceSimpleResponse(BaseModel):
    id: UUID
    student_id: UUID
    student_name: str
    present: bool
    observation: Optional[str] = None
    
    class Config:
        from_attributes = True

class GradeSimpleResponse(BaseModel):
    id: UUID
    student_id: UUID
    student_name: str
    value: float
    max_value: float
    observations: Optional[str] = None
    
    class Config:
        from_attributes = True

class LessonPlanDetailsResponse(BaseModel):
    attendance: list[AttendanceSimpleResponse] = []
    grades: list[GradeSimpleResponse] = []

class AttendanceUpdate(BaseModel):
    present: bool
    observation: Optional[str] = None

class GradeUpdate(BaseModel):
    value: float
    observations: Optional[str] = None
