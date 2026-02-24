"""
Auth Schemas
"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserInfo"


class UserInfo(BaseModel):
    id: UUID
    name: str
    email: str
    role: str
    tenant_id: Optional[UUID] = None
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True


class RefreshRequest(BaseModel):
    token: str


# Rebuild to resolve forward refs
TokenResponse.model_rebuild()
