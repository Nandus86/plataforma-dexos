"""
Auth Dependencies - FastAPI dependencies for authentication and authorization
"""
from typing import Optional, List
from uuid import UUID
from functools import wraps

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.auth.security import decode_access_token
from app.models.user import User, UserRole
from app.models.tenant import Tenant

security_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get the currently authenticated user from JWT token"""
    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado ou inativo",
        )

    return user


def require_role(*allowed_roles: UserRole):
    """Dependency factory: require user to have one of the allowed roles"""
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acesso negado. Papel necessário: {', '.join(r.value for r in allowed_roles)}",
            )
        return current_user
    return role_checker


async def get_current_tenant_id(
    current_user: User = Depends(get_current_user),
) -> Optional[UUID]:
    """Get the tenant_id from the current user (None for superadmin — used for listing)"""
    if current_user.role == UserRole.SUPERADMIN:
        return None  # Superadmin can access all tenants
    if current_user.tenant_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário não associado a nenhuma instituição",
        )
    return current_user.tenant_id


async def get_required_tenant_id(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UUID:
    """Get a guaranteed tenant_id — for create/write operations.
    Falls back to the first active tenant if the user (superadmin) has none."""
    if current_user.tenant_id:
        return current_user.tenant_id
    # Superadmin without tenant: pick first active tenant
    result = await db.execute(
        select(Tenant.id).where(Tenant.is_active == True).order_by(Tenant.created_at).limit(1)
    )
    tid = result.scalar_one_or_none()
    if tid is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhuma instituição cadastrada. Crie uma instituição primeiro.",
        )
    return tid
