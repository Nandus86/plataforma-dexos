"""
Course Models - Course, CurriculumMatrix, Subject, MatrixSubject
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Course(Base):
    """A course offered by a tenant (e.g., 'Teologia Básica')"""
    __tablename__ = "courses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    duration_semesters = Column(Integer, default=1)
    academic_period_id = Column(UUID(as_uuid=True), ForeignKey("academic_periods.id"), nullable=True, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant", back_populates="courses")
    curriculum_matrices = relationship("CurriculumMatrix", back_populates="course", lazy="selectin")
    class_groups = relationship("ClassGroup", back_populates="course", lazy="selectin")
    subjects = relationship("Subject", back_populates="course", lazy="selectin")
    enrollments = relationship("Enrollment", back_populates="course", lazy="selectin")
    academic_period = relationship("AcademicPeriod", back_populates="courses")

    def __repr__(self):
        return f"<Course {self.code} - {self.name}>"


class Subject(Base):
    """A subject/discipline that belongs to a course (e.g., 'Hermenêutica' in 'Teologia')"""
    __tablename__ = "subjects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id"), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False)
    workload_hours = Column(Integer, default=40)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    course = relationship("Course", back_populates="subjects")
    matrix_subjects = relationship("MatrixSubject", back_populates="subject")

    def __repr__(self):
        return f"<Subject {self.code} - {self.name}>"


class CurriculumMatrix(Base):
    """A curriculum matrix version for a course"""
    __tablename__ = "curriculum_matrices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)  # e.g., "Matriz 2026"
    year = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    course = relationship("Course", back_populates="curriculum_matrices")
    matrix_subjects = relationship("MatrixSubject", back_populates="matrix", lazy="selectin")

    def __repr__(self):
        return f"<CurriculumMatrix {self.name}>"


class MatrixSubject(Base):
    """Links a subject to a curriculum matrix with semester and professor"""
    __tablename__ = "matrix_subjects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    matrix_id = Column(UUID(as_uuid=True), ForeignKey("curriculum_matrices.id"), nullable=False, index=True)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False, index=True)
    professor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    semester = Column(Integer, nullable=False, default=1)
    is_active = Column(Boolean, default=True)

    # Relationships
    matrix = relationship("CurriculumMatrix", back_populates="matrix_subjects")
    subject = relationship("Subject", back_populates="matrix_subjects")
    professor = relationship("User", back_populates="taught_subjects", foreign_keys=[professor_id])
    lesson_plans = relationship("LessonPlan", back_populates="matrix_subject")
    materials = relationship("Material", back_populates="matrix_subject")
    assignments = relationship("Assignment", back_populates="matrix_subject")

    def __repr__(self):
        return f"<MatrixSubject matrix={self.matrix_id} subject={self.subject_id}>"
