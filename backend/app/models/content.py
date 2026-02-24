"""
Content Models - LessonPlan, Material, Announcement
"""
import uuid
import enum
from datetime import datetime

from sqlalchemy import Column, String, Boolean, DateTime, Enum, ForeignKey, Text, Integer, Float
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship

from app.database import Base


class AnnouncementTarget(str, enum.Enum):
    all = "all"
    course = "course"
    subject = "subject"


class ActivityType(str, enum.Enum):
    none = "none"
    exam = "exam"
    work = "work"
    other = "other"


class LessonPlan(Base):
    """Lesson plan created by a professor"""
    __tablename__ = "lesson_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    matrix_subject_id = Column(UUID(as_uuid=True), ForeignKey("matrix_subjects.id"), nullable=False, index=True)
    professor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    class_group_subject_id = Column(UUID(as_uuid=True), ForeignKey("class_group_subjects.id"), nullable=True, index=True)
    date = Column(DateTime, nullable=False)
    class_orders = Column(ARRAY(Integer), default=list)  # Ex: [1, 5] para 1ª e 5ª aula do dia
    topic = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)
    objectives = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    activity_type = Column(Enum(ActivityType), default=ActivityType.none)
    other_activity_reason = Column(Text, nullable=True)
    max_score = Column(Float, default=10.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    matrix_subject = relationship("MatrixSubject", back_populates="lesson_plans")
    professor = relationship("User", foreign_keys=[professor_id])
    class_group_subject = relationship("ClassGroupSubject")

    def __repr__(self):
        return f"<LessonPlan {self.topic}>"


class Material(Base):
    """Educational material shared by a professor"""
    __tablename__ = "materials"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    matrix_subject_id = Column(UUID(as_uuid=True), ForeignKey("matrix_subjects.id"), nullable=False, index=True)
    professor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    file_url = Column(String(500), nullable=True)
    file_type = Column(String(50), nullable=True)  # pdf, docx, video, link
    file_size = Column(String(50), nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    matrix_subject = relationship("MatrixSubject", back_populates="materials")
    professor = relationship("User", foreign_keys=[professor_id])

    def __repr__(self):
        return f"<Material {self.title}>"


class Announcement(Base):
    """Announcement/notice board post"""
    __tablename__ = "announcements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    target = Column(Enum(AnnouncementTarget), default=AnnouncementTarget.all)
    target_id = Column(UUID(as_uuid=True), nullable=True)  # course_id or subject_id if targeted
    pinned = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

    # Relationships
    author = relationship("User", foreign_keys=[author_id])

    def __repr__(self):
        return f"<Announcement {self.title}>"
