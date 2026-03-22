import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class BiometricData(Base):
    __tablename__ = "biometric_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True, index=True)
    
    biometric_type = Column(String(50), nullable=False)  # "fingerprint" or "face"
    finger_id = Column(Integer, nullable=True)           # 1-10 for fingerprint, None for face
    data = Column(Text, nullable=False)                  # base64 fingerData or faceData
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User")
    tenant = relationship("Tenant")

    def __repr__(self):
        return f"<BiometricData type={self.biometric_type} user_id={self.user_id}>"
