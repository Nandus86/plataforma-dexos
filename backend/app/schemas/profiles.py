"""
Profile Schemas - Students and Professionals
"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID
from datetime import date, datetime


# ==========================================
# Base Profile Models
# ==========================================
class ProfileBase(BaseModel):
    cpf: Optional[str] = None
    rg: Optional[str] = None
    birth_date: Optional[date] = None
    zip_code: Optional[str] = None
    street: Optional[str] = None
    number: Optional[str] = None
    neighborhood: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None


class StudentProfileData(ProfileBase):
    guardian_name: Optional[str] = None
    guardian_phone: Optional[str] = None
    guardian_email: Optional[EmailStr] = None
    previous_school: Optional[str] = None
    medical_conditions: Optional[str] = None


class ProfessionalProfileData(ProfileBase):
    job_title: Optional[str] = None
    hire_date: Optional[date] = None
    academic_qualifications: Optional[str] = None


# ==========================================
# Composite Creation Models 
# Used to create User + Profile in one API call
# ==========================================
class BaseUserCreate(BaseModel):
    name: str
    email: str
    password: str
    phone: Optional[str] = None
    registration_number: Optional[str] = None
    tenant_id: Optional[UUID] = None


class StudentCreate(BaseUserCreate):
    profile: Optional[StudentProfileData] = None


class ProfessionalCreate(BaseUserCreate):
    role: str  # Must be passed explicitly (e.g. "admin", "professor", "coordenacao")
    profile: Optional[ProfessionalProfileData] = None


# ==========================================
# Composite Update Models
# ==========================================
class BaseUserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    phone: Optional[str] = None
    registration_number: Optional[str] = None
    is_active: Optional[bool] = None


class StudentUpdate(BaseUserUpdate):
    profile: Optional[StudentProfileData] = None


class ProfessionalUpdate(BaseUserUpdate):
    role: Optional[str] = None
    profile: Optional[ProfessionalProfileData] = None


# ==========================================
# Response Models
# ==========================================
class StudentProfileResponse(StudentProfileData):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ProfessionalProfileResponse(ProfessionalProfileData):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class StudentResponse(BaseModel):
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
    
    student_profile: Optional[StudentProfileResponse] = None

    class Config:
        from_attributes = True


class ProfessionalResponse(BaseModel):
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

    professional_profile: Optional[ProfessionalProfileResponse] = None

    class Config:
        from_attributes = True


class StudentListResponse(BaseModel):
    users: list[StudentResponse]
    total: int


class ProfessionalListResponse(BaseModel):
    users: list[ProfessionalResponse]
    total: int
