"""
User Model - Multi-role authentication
"""
import uuid
import enum
from datetime import datetime

from sqlalchemy import Column, String, Boolean, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class UserRole(str, enum.Enum):
    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    COORDENACAO = "coordenacao"
    PROFESSOR = "professor"
    ESTUDANTE = "estudante"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.ESTUDANTE)
    registration_number = Column(String(50), nullable=True)  # Matrícula
    phone = Column(String(20), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    enrollments = relationship("Enrollment", back_populates="student", foreign_keys="Enrollment.student_id")
    taught_subjects = relationship("MatrixSubject", back_populates="professor", foreign_keys="MatrixSubject.professor_id")
    occurrences_received = relationship("Occurrence", back_populates="student", foreign_keys="Occurrence.student_id")
    occurrences_authored = relationship("Occurrence", back_populates="author", foreign_keys="Occurrence.author_id")

    # Linked Profiles (One-to-One)
    student_profile = relationship("StudentProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    professional_profile = relationship("ProfessionalProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")

    # Unique constraint per tenant
    __table_args__ = (
        # A user email must be unique within a tenant (or globally for superadmin)
    )

    def __repr__(self):
        return f"<User {self.name} ({self.role.value})>"
