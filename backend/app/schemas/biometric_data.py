from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class BiometricDataBase(BaseModel):
    biometric_type: str
    finger_id: Optional[int] = None
    data: str


class BiometricDataCreate(BiometricDataBase):
    user_id: UUID


class BiometricDataResponse(BiometricDataBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True
