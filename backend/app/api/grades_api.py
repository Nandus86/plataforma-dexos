"""
Grades API Router - Mounted at /grades
Provides CRUD for grade records.
"""
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User, UserRole
from app.models.academic import Grade
from app.auth.dependencies import get_current_user, require_role
from app.schemas.academic import GradeCreate, GradeUpdate, GradeResponse

router = APIRouter()


@router.get("/", response_model=list[GradeResponse])
async def list_grades(
    enrollment_id: Optional[UUID] = None,
    lesson_plan_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Grade)
    if enrollment_id:
        query = query.where(Grade.enrollment_id == enrollment_id)
    if lesson_plan_id:
        query = query.where(Grade.lesson_plan_id == lesson_plan_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=GradeResponse, status_code=status.HTTP_201_CREATED)
async def create_grade(
    data: GradeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.PROFESSOR)),
):
    grade = Grade(**data.model_dump())
    db.add(grade)
    await db.commit()
    await db.refresh(grade)
    return grade


@router.put("/{grade_id}", response_model=GradeResponse)
async def update_grade(
    grade_id: UUID,
    data: GradeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.PROFESSOR)),
):
    result = await db.execute(select(Grade).where(Grade.id == grade_id))
    grade = result.scalar_one_or_none()
    if not grade:
        raise HTTPException(status_code=404, detail="Nota não encontrada")
    
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(grade, key, value)
    
    await db.commit()
    await db.refresh(grade)
    return grade
