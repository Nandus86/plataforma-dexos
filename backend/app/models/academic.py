"""
Academic Models - Enrollment, Grade, Attendance, Assignment, AssignmentSubmission
"""
import uuid
import enum
from datetime import datetime

from sqlalchemy import Column, String, Boolean, DateTime, Integer, Float, Enum, ForeignKey, Text, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class EnrollmentStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    LOCKED = "locked"
    INACTIVE = "inactive"
    TRANSFERRED = "transferred"


enrollment_period_breaks = Table(
    "enrollment_period_breaks",
    Base.metadata,
    Column("enrollment_id", UUID(as_uuid=True), ForeignKey("enrollments.id", ondelete="CASCADE"), primary_key=True),
    Column("period_break_id", UUID(as_uuid=True), ForeignKey("period_breaks.id", ondelete="CASCADE"), primary_key=True)
)


class Enrollment(Base):
    """Student enrollment in a course"""
    __tablename__ = "enrollments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False, index=True)
    year = Column(Integer, nullable=False)
    academic_period_id = Column(UUID(as_uuid=True), ForeignKey("academic_periods.id"), nullable=False, index=True)
    enrollment_code = Column(String(50), nullable=True, unique=True, index=True)
    status = Column(Enum(EnrollmentStatus), default=EnrollmentStatus.ACTIVE)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    student = relationship("User", back_populates="enrollments", foreign_keys=[student_id])
    course = relationship("Course", back_populates="enrollments")
    academic_period = relationship("app.models.academic_period.AcademicPeriod")
    period_breaks = relationship("app.models.academic_period.PeriodBreak", secondary=enrollment_period_breaks, lazy="selectin")
    grades = relationship("Grade", back_populates="enrollment", lazy="selectin")
    attendances = relationship("Attendance", back_populates="enrollment", lazy="selectin")

    def __repr__(self):
        return f"<Enrollment student={self.student_id} course={self.course_id} period={self.academic_period_id}>"


class Grade(Base):
    """Grade/evaluation for an enrollment"""
    __tablename__ = "grades"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    enrollment_id = Column(UUID(as_uuid=True), ForeignKey("enrollments.id"), nullable=False, index=True)
    lesson_plan_id = Column(UUID(as_uuid=True), ForeignKey("lesson_plans.id"), nullable=True, index=True)
    evaluation_name = Column(String(255), nullable=False)  # e.g., "Prova 1", "Trabalho Final"
    value = Column(Float, nullable=False)
    max_value = Column(Float, default=10.0)
    date = Column(DateTime, nullable=True)
    observations = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    enrollment = relationship("Enrollment", back_populates="grades")
    lesson_plan = relationship("app.models.content.LessonPlan")

    def __repr__(self):
        return f"<Grade {self.evaluation_name}: {self.value}/{self.max_value}>"


class Attendance(Base):
    """Attendance record for a class session"""
    __tablename__ = "attendances"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    enrollment_id = Column(UUID(as_uuid=True), ForeignKey("enrollments.id"), nullable=False, index=True)
    lesson_plan_id = Column(UUID(as_uuid=True), ForeignKey("lesson_plans.id"), nullable=True, index=True)
    class_date = Column(DateTime, nullable=False)
    class_order_item = Column(Integer, nullable=True)  # Referência a qual aula (1ª, 2ª) do array do lesson_plan_id foi registrada
    present = Column(Boolean, default=False)
    checkin_method = Column(String(50), default="manual")  # manual, qrcode, biometric, api
    observation = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    enrollment = relationship("Enrollment", back_populates="attendances")
    lesson_plan = relationship("app.models.content.LessonPlan")

    def __repr__(self):
        return f"<Attendance date={self.class_date} present={self.present}>"


class Assignment(Base):
    """Assignment/task created by a professor for a subject"""
    __tablename__ = "assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    matrix_subject_id = Column(UUID(as_uuid=True), ForeignKey("matrix_subjects.id"), nullable=False, index=True)
    professor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(DateTime, nullable=True)
    max_score = Column(Float, default=10.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    matrix_subject = relationship("MatrixSubject", back_populates="assignments")
    professor = relationship("User", foreign_keys=[professor_id])
    submissions = relationship("AssignmentSubmission", back_populates="assignment", lazy="selectin")

    def __repr__(self):
        return f"<Assignment {self.title}>"


class AssignmentSubmission(Base):
    """Student submission for an assignment"""
    __tablename__ = "assignment_submissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assignment_id = Column(UUID(as_uuid=True), ForeignKey("assignments.id"), nullable=False, index=True)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    content = Column(Text, nullable=True)
    file_url = Column(String(500), nullable=True)
    score = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    graded_at = Column(DateTime, nullable=True)

    # Relationships
    assignment = relationship("Assignment", back_populates="submissions")
    student = relationship("User", foreign_keys=[student_id])

    def __repr__(self):
        return f"<AssignmentSubmission assignment={self.assignment_id} student={self.student_id}>"
