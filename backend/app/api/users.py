"""
Users API - CRUD with role and tenant filtering
"""
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserListResponse
from app.auth.security import hash_password
from app.auth.dependencies import get_current_user, require_role, get_current_tenant_id

router = APIRouter()


@router.get("/", response_model=UserListResponse)
async def list_users(
    role: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    target_tenant_id: Optional[UUID] = Query(None, description="Optional tenant filter for superadmins"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.PROFESSOR, UserRole.COORDENACAO)),
    tenant_id: Optional[UUID] = Depends(get_current_tenant_id),
):
    """List users with optional filtering"""
    query = select(User)

    # Tenant isolation
    # If superadmin requested a specific tenant, use it. Otherwise, use context tenant.
    effective_tenant_id = target_tenant_id if (target_tenant_id and current_user.role == UserRole.SUPERADMIN) else tenant_id
    
    if effective_tenant_id:
        query = query.where(User.tenant_id == effective_tenant_id)

    if role:
        try:
            role_enum = UserRole(role)
            query = query.where(User.role == role_enum)
        except ValueError:
            pass  # Invalid role string, skip filter

    if search:
        query = query.where(User.name.ilike(f"%{search}%"))

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    # Paginate
    query = query.order_by(User.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    users = result.scalars().all()

    return UserListResponse(users=users, total=total)


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN)),
    tenant_id: Optional[UUID] = Depends(get_current_tenant_id),
):
    """Create a new user"""
    # Check email uniqueness within tenant
    existing_query = select(User).where(User.email == data.email)
    if tenant_id:
        existing_query = existing_query.where(User.tenant_id == tenant_id)
    existing = await db.execute(existing_query)
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email já cadastrado")

    # Only superadmin can create admin/superadmin users
    if data.role in ["superadmin", "admin"] and current_user.role != UserRole.SUPERADMIN:
        if data.role == "superadmin":
            raise HTTPException(status_code=403, detail="Apenas superadmin pode criar outros superadmins")

    from app.core.registration import generate_registration_number

    # Generate registration code
    try:
        reg_number = data.registration_number or await generate_registration_number(db, UserRole(data.role), data.tenant_id or tenant_id)
    except Exception as e:
        reg_number = None

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
    await db.commit()
    await db.refresh(user)
    return user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN)),
):
    """Get user by ID"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN)),
):
    """Update user"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    update_data = data.model_dump(exclude_unset=True)
    if "password" in update_data:
        update_data["password_hash"] = hash_password(update_data.pop("password"))

    for key, value in update_data.items():
        if key == "role":
            setattr(user, key, UserRole(value))
        else:
            setattr(user, key, value)

    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN)),
):
    """Deactivate a user"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    user.is_active = False
    await db.commit()
