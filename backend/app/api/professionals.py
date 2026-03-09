"""
Professionals API - CRUD for Staff (Admins, Coordinators, Professors) and their detailed profiles
"""
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.user import User, UserRole
from app.models.profiles import ProfessionalProfile
from app.schemas.profiles import ProfessionalCreate, ProfessionalUpdate, ProfessionalResponse, ProfessionalListResponse
from app.auth.security import hash_password
from app.auth.dependencies import get_current_user, require_role, get_current_tenant_id

router = APIRouter()


@router.get("/", response_model=ProfessionalListResponse)
async def list_professionals(
    role: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(1000, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.COORDENACAO)),
    tenant_id: Optional[UUID] = Depends(get_current_tenant_id),
):
    """List all professionals (non-students) for the current tenant"""
    query = select(User).options(selectinload(User.professional_profile)).where(User.role != UserRole.ESTUDANTE)

    if tenant_id:
        query = query.where(User.tenant_id == tenant_id)

    if role:
        query = query.where(User.role == role)

    if search:
        query = query.where(User.name.ilike(f"%{search}%"))

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    # Paginate
    query = query.order_by(User.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    users = result.scalars().all()

    return ProfessionalListResponse(users=users, total=total)


@router.post("/", response_model=ProfessionalResponse, status_code=status.HTTP_201_CREATED)
async def create_professional(
    data: ProfessionalCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.COORDENACAO)),
    tenant_id: Optional[UUID] = Depends(get_current_tenant_id),
):
    """Create a new professional with a detailed profile"""
    # Prevent creating students from this endpoint
    if data.role == "estudante":
        raise HTTPException(status_code=400, detail="Use o endpoint de estudantes para criar estudantes.")

    # Only superadmin can create admin/superadmin users
    if data.role in ["superadmin", "admin"] and current_user.role != UserRole.SUPERADMIN:
        if data.role == "superadmin":
            raise HTTPException(status_code=403, detail="Apenas superadmin pode criar outros superadmins")

    # Check email uniqueness within tenant
    existing_query = select(User).where(User.email == data.email)
    if tenant_id:
        existing_query = existing_query.where(User.tenant_id == tenant_id)
    existing = await db.execute(existing_query)
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email já cadastrado")

    from app.core.registration import generate_registration_number

    # Generate registration code
    try:
        reg_number = data.registration_number or await generate_registration_number(db, UserRole(data.role), data.tenant_id or tenant_id)
    except Exception as e:
        reg_number = None

    # Create User
    user = User(
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
        role=UserRole(data.role),
        registration_number=reg_number,
        phone=data.phone,
        tenant_id=data.tenant_id or tenant_id,
    )
    db.add(user)
    await db.flush()  # Gets the user ID

    # Create Profile
    profile_data = data.profile.model_dump() if data.profile else {}
    profile = ProfessionalProfile(user_id=user.id, **profile_data)
    db.add(profile)

    await db.commit()
    result = await db.execute(select(User).options(selectinload(User.professional_profile)).where(User.id == user.id))
    return result.scalar_one()


@router.get("/{user_id}", response_model=ProfessionalResponse)
async def get_professional(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.COORDENACAO)),
):
    """Get professional by ID including profile"""
    result = await db.execute(select(User).options(selectinload(User.professional_profile)).where(User.id == user_id, User.role != UserRole.ESTUDANTE))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Profissional não encontrado")

    return user


@router.put("/{user_id}", response_model=ProfessionalResponse)
async def update_professional(
    user_id: UUID,
    data: ProfessionalUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.COORDENACAO)),
):
    """Update professional base data and their detailed profile"""
    result = await db.execute(select(User).options(selectinload(User.professional_profile)).where(User.id == user_id, User.role != UserRole.ESTUDANTE))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Profissional não encontrado")

    # Update User Level Data
    update_data = data.model_dump(exclude_unset=True, exclude={"profile"})
    for key, value in update_data.items():
        if key == "password":
            user.password_hash = hash_password(value)
        else:
            setattr(user, key, value)

    # Update Profile Level Data
    if data.profile:
        if not user.professional_profile:
            user.professional_profile = ProfessionalProfile(user_id=user.id)
            db.add(user.professional_profile)
            
        profile_update = data.profile.model_dump(exclude_unset=True)
        for key, value in profile_update.items():
            setattr(user.professional_profile, key, value)

    await db.commit()
    result = await db.execute(select(User).options(selectinload(User.professional_profile)).where(User.id == user.id))
    return result.scalar_one()
