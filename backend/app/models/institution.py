"""
Institution Model - Educational entity details linked to a Tenant
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Institution(Base):
    __tablename__ = "institutions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    
    # Informações institucionais
    name = Column(String(255), nullable=False)
    cnpj = Column(String(20), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    principal_name = Column(String(255), nullable=True)
    
    # Endereço
    address_street = Column(String(255), nullable=True)
    address_number = Column(String(20), nullable=True)
    address_complement = Column(String(255), nullable=True)
    address_neighborhood = Column(String(255), nullable=True)
    address_city = Column(String(255), nullable=True)
    address_state = Column(String(2), nullable=True)
    address_zip = Column(String(20), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant", back_populates="institution", lazy="selectin")

    def __repr__(self):
        return f"<Institution {self.name}>"
