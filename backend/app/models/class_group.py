"""
Class Group Models - ClassGroup (Turma), ClassGroupStudent, ClassGroupSubject, ClassGroupStudentSubject, ClassGroupSubjectProfessor
"""
import uuid
import enum
from datetime import datetime

from sqlalchemy import Column, String, Boolean, DateTime, Integer, Enum, ForeignKey, Text, UniqueConstraint, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class ShiftType(str, enum.Enum):
    MANHA = "manha"
    TARDE = "tarde"
    NOITE = "noite"
    INTEGRAL = "integral"


class ClassGroup(Base):
    """A class group (turma) that links a course, year, semester, and shift"""
    __tablename__ = "class_groups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    academic_period_id = Column(UUID(as_uuid=True), ForeignKey("academic_periods.id"), nullable=True, index=True)
    period_break_id = Column(UUID(as_uuid=True), ForeignKey("period_breaks.id"), nullable=True, index=True)  # Null = All period
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)  # e.g., "Teologia Básica 2026.1 - Noturno"
    year = Column(Integer, nullable=False)
    semester = Column(Integer, nullable=True)
    shift = Column(Enum(ShiftType), default=ShiftType.NOITE)
    max_students = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant")
    academic_period = relationship("AcademicPeriod")
    period_break = relationship("PeriodBreak")
    course = relationship("Course", back_populates="class_groups")
    students = relationship("ClassGroupStudent", back_populates="class_group", lazy="selectin", cascade="all, delete-orphan")
    subjects = relationship("ClassGroupSubject", back_populates="class_group", lazy="selectin", cascade="all, delete-orphan")
    student_subjects = relationship("ClassGroupStudentSubject", back_populates="class_group", lazy="selectin", cascade="all, delete-orphan")
    class_schedules = relationship("ClassSchedule", back_populates="class_group", lazy="selectin", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ClassGroup {self.name}>"


class ClassGroupStudent(Base):
    """Links an enrollment (student in a course) to a class group"""
    __tablename__ = "class_group_students"
    __table_args__ = (
        UniqueConstraint("class_group_id", "enrollment_id", name="uq_cg_enrollment"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    class_group_id = Column(UUID(as_uuid=True), ForeignKey("class_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    enrollment_id = Column(UUID(as_uuid=True), ForeignKey("enrollments.id", ondelete="CASCADE"), nullable=False, index=True)
    enrolled_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    class_group = relationship("ClassGroup", back_populates="students")
    enrollment = relationship("Enrollment", foreign_keys=[enrollment_id])

    def __repr__(self):
        return f"<ClassGroupStudent group={self.class_group_id} enrollment={self.enrollment_id}>"


class ClassGroupSubject(Base):
    """Links a subject directly to a class group"""
    __tablename__ = "class_group_subjects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    class_group_id = Column(UUID(as_uuid=True), ForeignKey("class_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    period_break_id = Column(UUID(as_uuid=True), ForeignKey("period_breaks.id"), nullable=True, index=True)  # Null = All period (or inherited from class group)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False, index=True)
    # professor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)  <-- DEPRECATED

    # Relationships
    class_group = relationship("ClassGroup", back_populates="subjects")
    period_break = relationship("PeriodBreak")
    subject = relationship("Subject")
    # professor = relationship("User", foreign_keys=[professor_id])  <-- DEPRECATED
    professors = relationship("ClassGroupSubjectProfessor", back_populates="class_group_subject", lazy="selectin", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ClassGroupSubject group={self.class_group_id} subject={self.subject_id}>"


class ClassGroupSubjectProfessor(Base):
    """Pivot: Links a professor to a class group subject with assigned hours"""
    __tablename__ = "class_group_subject_professors"
    __table_args__ = (
        UniqueConstraint("class_group_subject_id", "professor_id", name="uq_cgs_professor"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    class_group_subject_id = Column(UUID(as_uuid=True), ForeignKey("class_group_subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    professor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    assigned_hours = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    class_group_subject = relationship("ClassGroupSubject", back_populates="professors")
    professor = relationship("User", foreign_keys=[professor_id])

    def __repr__(self):
        return f"<ClassGroupSubjectProfessor subject={self.class_group_subject_id} professor={self.professor_id}>"


class ClassGroupStudentSubject(Base):
    """Pivot: tracks an enrollment's status in a specific subject within a class group"""
    __tablename__ = "class_group_student_subjects"
    __table_args__ = (
        UniqueConstraint("class_group_id", "enrollment_id", "subject_id", name="uq_cg_enrollment_subject"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    class_group_id = Column(UUID(as_uuid=True), ForeignKey("class_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    enrollment_id = Column(UUID(as_uuid=True), ForeignKey("enrollments.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    class_group = relationship("ClassGroup", back_populates="student_subjects")
    enrollment = relationship("Enrollment", foreign_keys=[enrollment_id])
    subject = relationship("Subject")

    def __repr__(self):
        return f"<ClassGroupStudentSubject group={self.class_group_id} enrollment={self.enrollment_id} subject={self.subject_id}>"


class ClassSchedule(Base):
    """Horários das aulas no dia de uma turma específica"""
    __tablename__ = "class_schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    class_group_id = Column(UUID(as_uuid=True), ForeignKey("class_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    order = Column(Integer, nullable=False)  # 1ª aula, 2ª aula, etc
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    duration_minutes = Column(Integer, nullable=True)  # Calculado automaticamente

    # Relationships
    class_group = relationship("ClassGroup", back_populates="class_schedules")

    def __repr__(self):
        return f"<ClassSchedule {self.order}ª aula: {self.start_time} - {self.end_time}>"
