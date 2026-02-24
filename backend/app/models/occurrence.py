"""
Occurrence Model - Praise, warnings, complaints, observations
"""
import uuid
import enum
from datetime import datetime

from sqlalchemy import Column, String, Boolean, DateTime, Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class OccurrenceType(str, enum.Enum):
    PRAISE = "praise"          # Elogio
    WARNING = "warning"        # Advertência
    COMPLAINT = "complaint"    # Reclamação
    OBSERVATION = "observation" # Observação


class Occurrence(Base):
    """Student occurrence record"""
    __tablename__ = "occurrences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    type = Column(Enum(OccurrenceType), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    date = Column(DateTime, default=datetime.utcnow)
    parent_notified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    student = relationship("User", back_populates="occurrences_received", foreign_keys=[student_id])
    author = relationship("User", back_populates="occurrences_authored", foreign_keys=[author_id])

    def __repr__(self):
        return f"<Occurrence {self.type.value}: {self.title}>"
