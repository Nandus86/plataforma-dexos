"""
Tenants API - CRUD (superadmin only)
"""
from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.tenant import Tenant
from app.models.user import User, UserRole
from app.schemas.tenant import TenantCreate, TenantUpdate, TenantResponse
from app.auth.dependencies import get_current_user, require_role

router = APIRouter()


@router.get("/", response_model=list[TenantResponse])
async def list_tenants(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN)),
):
    """List all tenants (superadmin only)"""
    result = await db.execute(select(Tenant).order_by(Tenant.created_at.desc()))
    return result.scalars().all()


@router.post("/", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    data: TenantCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN)),
):
    """Create a new tenant"""
    # Check slug uniqueness
    existing = await db.execute(select(Tenant).where(Tenant.slug == data.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Slug já existe")

    tenant = Tenant(**data.model_dump())
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)
    return tenant


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN)),
):
    """Get tenant by ID"""
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Instituição não encontrada")
    return tenant


@router.put("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: UUID,
    data: TenantUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN)),
):
    """Update tenant"""
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Instituição não encontrada")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(tenant, key, value)

    await db.commit()
    await db.refresh(tenant)
    return tenant


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN)),
):
    """Deactivate a tenant"""
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Instituição não encontrada")

    tenant.is_active = False
    await db.commit()


@router.get("/{tenant_id}/features", response_model=dict)
async def get_tenant_features(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get tenant features matrix"""
    # specific permission check
    if current_user.role != UserRole.SUPERADMIN and str(current_user.tenant_id) != str(tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Acesso negado a esta instituição"
        )

    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Instituição não encontrada")

    import json
    from app.core.features import get_default_settings

    # If no settings, return defaults
    if not tenant.settings_json:
        return get_default_settings()

    try:
        settings = json.loads(tenant.settings_json)
        # Verify if needs migration/merge with defaults
        defaults = get_default_settings()
        
        # Merge logic could be here, for now just returning what is stored or defaults
        if "features" not in settings:
            return defaults
            
        merged_features = defaults["features"].copy()
        
        # Merge saved values over defaults, but keep labels/descriptions intact
        for key, saved_val in settings["features"].items():
            if key in merged_features:
                merged_features[key]["enabled"] = saved_val.get("enabled", True)
                merged_features[key]["roles"] = saved_val.get("roles", merged_features[key]["roles"])
                
        # Return cleanly
        return {"features": merged_features}
                
    except json.JSONDecodeError:
        return get_default_settings()


@router.put("/{tenant_id}/features", response_model=dict)
async def update_tenant_features(
    tenant_id: UUID,
    features: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN)),
):
    """Update tenant features matrix"""
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Instituição não encontrada")

    import json
    
    # Simple validation could go here
    
    tenant.settings_json = json.dumps(features)
    tenant.updated_at = datetime.utcnow()
    
    await db.commit()
    return features

