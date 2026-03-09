"""
Students API - CRUD for Students and their detailed profiles
"""
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.user import User, UserRole
from app.models.profiles import StudentProfile
from app.schemas.profiles import StudentCreate, StudentUpdate, StudentResponse, StudentListResponse
from app.auth.security import hash_password
from app.auth.dependencies import get_current_user, require_role, get_current_tenant_id

router = APIRouter()


@router.get("/", response_model=StudentListResponse)
async def list_students(
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(1000, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.COORDENACAO, UserRole.PROFESSOR)),
    tenant_id: Optional[UUID] = Depends(get_current_tenant_id),
):
    """List all students for the current tenant"""
    query = select(User).options(selectinload(User.student_profile)).where(User.role == UserRole.ESTUDANTE)

    if tenant_id:
        query = query.where(User.tenant_id == tenant_id)

    if search:
        query = query.where(User.name.ilike(f"%{search}%"))

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    # Paginate
    query = query.order_by(User.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    users = result.scalars().all()

    return StudentListResponse(users=users, total=total)


@router.post("/", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
async def create_student(
    data: StudentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.COORDENACAO)),
    tenant_id: Optional[UUID] = Depends(get_current_tenant_id),
):
    """Create a new student with a detailed profile"""
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
        reg_number = data.registration_number or await generate_registration_number(db, UserRole.ESTUDANTE, data.tenant_id or tenant_id)
    except Exception as e:
        reg_number = None

    # Create User
    user = User(
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
        role=UserRole.ESTUDANTE,
        registration_number=reg_number,
        phone=data.phone,
        tenant_id=data.tenant_id or tenant_id,
    )
    db.add(user)
    await db.flush()  # Gets the user ID

    # Create Profile
    profile_data = data.profile.model_dump() if data.profile else {}
    profile = StudentProfile(user_id=user.id, **profile_data)
    db.add(profile)

    await db.commit()
    result = await db.execute(select(User).options(selectinload(User.student_profile)).where(User.id == user.id))
    new_student = result.scalar_one()

    # --- INÍCIO DA INTEGRAÇÃO BIOMETRIA ---
    try:
        import httpx
        import asyncio
        import logging
        from app.config import settings as app_settings
        logger = logging.getLogger(__name__)

        async def send_to_biometrics(ra, name):
            try:
                bio_url = f"{app_settings.BIOMETRICS_SERVICE_URL}/device/users"
                async with httpx.AsyncClient(timeout=10.0) as client:
                    await client.post(
                        bio_url,
                        json={"employee_no": str(ra), "name": name}
                    )
                    logger.info(f"Aluno {name} ({ra}) enfileirado para envio ao relógio Hikvision")
            except Exception as e:
                logger.error(f"Falha ao enviar aluno para o relógio: {e}")

        asyncio.create_task(send_to_biometrics(new_student.registration_number, new_student.name))
    except Exception as e:
        pass
    # --- FIM DA INTEGRAÇÃO ---

    return new_student


@router.get("/{user_id}", response_model=StudentResponse)
async def get_student(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.COORDENACAO, UserRole.PROFESSOR)),
):
    """Get student by ID including profile"""
    # Ensure role is estudante
    result = await db.execute(select(User).options(selectinload(User.student_profile)).where(User.id == user_id, User.role == UserRole.ESTUDANTE))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Estudante não encontrado")

    return user


@router.put("/{user_id}", response_model=StudentResponse)
async def update_student(
    user_id: UUID,
    data: StudentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.COORDENACAO)),
):
    """Update student base data and their detailed profile"""
    result = await db.execute(select(User).options(selectinload(User.student_profile)).where(User.id == user_id, User.role == UserRole.ESTUDANTE))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Estudante não encontrado")

    # Update User Level Data
    update_data = data.model_dump(exclude_unset=True, exclude={"profile"})
    for key, value in update_data.items():
        if key == "password":
            user.password_hash = hash_password(value)
        else:
            setattr(user, key, value)

    # Update Profile Level Data
    if data.profile:
        if not user.student_profile:
            user.student_profile = StudentProfile(user_id=user.id)
            db.add(user.student_profile)
            
        profile_update = data.profile.model_dump(exclude_unset=True)
        for key, value in profile_update.items():
            setattr(user.student_profile, key, value)

    await db.commit()
    result = await db.execute(select(User).options(selectinload(User.student_profile)).where(User.id == user.id))
    return result.scalar_one()
