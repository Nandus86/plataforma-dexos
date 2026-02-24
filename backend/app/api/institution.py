"""
Institution API - View and update by Admin of the same tenant
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.institution import Institution
from app.models.tenant import Tenant
from app.models.user import User, UserRole
from app.schemas.institution import InstitutionUpdate, InstitutionResponse
from app.auth.dependencies import get_current_user, require_role, get_current_tenant_id

router = APIRouter()

async def get_or_create_institution(db: AsyncSession, tenant_id: UUID) -> Institution:
    result = await db.execute(select(Institution).where(Institution.tenant_id == tenant_id))
    institution = result.scalar_one_or_none()
    
    if not institution:
        # Pega o nome do tenant como default para criar
        tenant_res = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
        tenant = tenant_res.scalar_one_or_none()
        institution = Institution(tenant_id=tenant_id, name=tenant.name if tenant else "Instituição")
        db.add(institution)
        await db.commit()
        await db.refresh(institution)
        
    return institution

@router.get("/me", response_model=InstitutionResponse)
async def get_my_institution(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.SUPERADMIN)),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    """Get current user's institution details"""
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Usuário não vinculado a uma instituição")
        
    return await get_or_create_institution(db, tenant_id)


@router.put("/me", response_model=InstitutionResponse)
async def update_my_institution(
    data: InstitutionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.SUPERADMIN)),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    """Update current user's institution details"""
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Usuário não vinculado a uma instituição")
        
    institution = await get_or_create_institution(db, tenant_id)

    update_data = data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(institution, key, value)

    await db.commit()
    await db.refresh(institution)
    return institution
