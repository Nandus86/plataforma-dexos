"""
Occurrences API - Praise, warnings, complaints, observations
"""
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User, UserRole
from app.models.occurrence import Occurrence, OccurrenceType
from app.schemas.occurrence import OccurrenceCreate, OccurrenceUpdate, OccurrenceResponse
from app.auth.dependencies import get_current_user, require_role, get_current_tenant_id, get_required_tenant_id

router = APIRouter()


@router.get("/", response_model=list[OccurrenceResponse])
async def list_occurrences(
    student_id: Optional[UUID] = None,
    type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: Optional[UUID] = Depends(get_current_tenant_id),
):
    """List occurrences. Students see only their own."""
    query = select(Occurrence)

    if tenant_id:
        query = query.where(Occurrence.tenant_id == tenant_id)

    if current_user.role == UserRole.ESTUDANTE:
        query = query.where(Occurrence.student_id == current_user.id)
    elif student_id:
        query = query.where(Occurrence.student_id == student_id)

    if type:
        query = query.where(Occurrence.type == type)

    result = await db.execute(query.order_by(Occurrence.created_at.desc()))
    return result.scalars().all()


@router.post("/", response_model=OccurrenceResponse, status_code=status.HTTP_201_CREATED)
async def create_occurrence(
    data: OccurrenceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.PROFESSOR, UserRole.COORDENACAO)),
    tenant_id: UUID = Depends(get_required_tenant_id),
):
    """Create an occurrence (professor or admin)"""
    occurrence = Occurrence(
        tenant_id=tenant_id,
        student_id=data.student_id,
        author_id=current_user.id,
        type=OccurrenceType(data.type),
        title=data.title,
        description=data.description,
        date=data.date,
    )
    db.add(occurrence)
    await db.commit()
    await db.refresh(occurrence)
    return occurrence


@router.get("/{occurrence_id}", response_model=OccurrenceResponse)
async def get_occurrence(
    occurrence_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Occurrence).where(Occurrence.id == occurrence_id))
    occurrence = result.scalar_one_or_none()
    if not occurrence:
        raise HTTPException(status_code=404, detail="Ocorrência não encontrada")
    # Students can only see their own
    if current_user.role == UserRole.ESTUDANTE and occurrence.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Acesso negado")
    return occurrence


@router.put("/{occurrence_id}", response_model=OccurrenceResponse)
async def update_occurrence(
    occurrence_id: UUID,
    data: OccurrenceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.PROFESSOR, UserRole.COORDENACAO)),
):
    result = await db.execute(select(Occurrence).where(Occurrence.id == occurrence_id))
    occurrence = result.scalar_one_or_none()
    if not occurrence:
        raise HTTPException(status_code=404, detail="Ocorrência não encontrada")

    update_data = data.model_dump(exclude_unset=True)
    if "type" in update_data:
        update_data["type"] = OccurrenceType(update_data["type"])

    for key, value in update_data.items():
        setattr(occurrence, key, value)

    await db.commit()
    await db.refresh(occurrence)
    return occurrence


@router.delete("/{occurrence_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_occurrence(
    occurrence_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN)),
):
    result = await db.execute(select(Occurrence).where(Occurrence.id == occurrence_id))
    occurrence = result.scalar_one_or_none()
    if not occurrence:
        raise HTTPException(status_code=404, detail="Ocorrência não encontrada")
    await db.delete(occurrence)
    await db.commit()
