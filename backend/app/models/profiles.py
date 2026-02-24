import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base

class StudentProfile(Base):
    """
    Detailed profile for students, linked to the main User table.
    Contains personal, address, parent, and previous academic history data.
    """
    __tablename__ = "student_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)

    # Personal Documents
    cpf = Column(String(20), nullable=True)
    rg = Column(String(20), nullable=True)
    birth_date = Column(Date, nullable=True)

    # Address
    zip_code = Column(String(20), nullable=True)
    street = Column(String(255), nullable=True)
    number = Column(String(50), nullable=True)
    neighborhood = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(50), nullable=True)

    # Guardian (Parents)
    guardian_name = Column(String(255), nullable=True)
    guardian_phone = Column(String(20), nullable=True)
    guardian_email = Column(String(255), nullable=True)

    # Academic / Medical
    previous_school = Column(String(255), nullable=True)
    medical_conditions = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship back to user
    user = relationship("User", back_populates="student_profile")


class ProfessionalProfile(Base):
    """
    Detailed profile for staff (Admins, Coordinators, Professors), linked to main User table.
    Contains personal, address, job, and academic qualifications data.
    """
    __tablename__ = "professional_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)

    # Personal Documents
    cpf = Column(String(20), nullable=True)
    rg = Column(String(20), nullable=True)
    birth_date = Column(Date, nullable=True)

    # Address
    zip_code = Column(String(20), nullable=True)
    street = Column(String(255), nullable=True)
    number = Column(String(50), nullable=True)
    neighborhood = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(50), nullable=True)

    # Professional Details
    job_title = Column(String(100), nullable=True)
    hire_date = Column(Date, nullable=True)
    academic_qualifications = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship back to user
    user = relationship("User", back_populates="professional_profile")
