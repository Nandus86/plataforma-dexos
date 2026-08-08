"""
User Schemas
"""
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class UserCreate(BaseModel):
    name: str
    email: str
    password: Optional[str] = None
    role: str = "estudante"
    registration_number: Optional[str] = None
    phone: Optional[str] = None
    tenant_id: Optional[UUID] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    registration_number: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None
    avatar_url: Optional[str] = None


class UserResponse(BaseModel):
    id: UUID
    name: str
    email: str
    role: str
    registration_number: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    tenant_id: Optional[UUID] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    users: list[UserResponse]
    total: int

class UserCreateResponse(UserResponse):
    initial_password: Optional[str] = None

class PasswordChange(BaseModel):
    old_password: str
    new_password: str

class PasswordResetResponse(BaseModel):
    message: str
    new_password: str
