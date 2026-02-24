"""
Tenant Model - Multi-tenancy support
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    domain = Column(String(255), nullable=True, unique=True)
    is_active = Column(Boolean, default=True)
    settings_json = Column(Text, nullable=True)  # JSON string for tenant-specific settings
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    institution = relationship("Institution", back_populates="tenant", uselist=False, lazy="selectin", cascade="all, delete-orphan")
    users = relationship("User", back_populates="tenant", lazy="selectin")
    courses = relationship("Course", back_populates="tenant", lazy="selectin")

    def __repr__(self):
        return f"<Tenant {self.name}>"
