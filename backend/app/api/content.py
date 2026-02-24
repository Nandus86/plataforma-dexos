"""
Content API - Lesson Plans, Materials, Announcements
"""
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User, UserRole
from app.models.content import LessonPlan, Material, Announcement, AnnouncementTarget
from app.schemas.content import (
    LessonPlanCreate, LessonPlanUpdate, LessonPlanResponse,
    MaterialCreate, MaterialResponse,
    AnnouncementCreate, AnnouncementUpdate, AnnouncementResponse,
)
from app.models.academic import Enrollment, Attendance, Grade
from app.auth.dependencies import get_current_user, require_role, get_current_tenant_id, get_required_tenant_id

router = APIRouter()


# ========== LESSON PLANS ==========

@router.get("/lesson-plans/", response_model=list[LessonPlanResponse])
async def list_lesson_plans(
    matrix_subject_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(LessonPlan)
    if matrix_subject_id:
        query = query.where(LessonPlan.matrix_subject_id == matrix_subject_id)
    if current_user.role == UserRole.PROFESSOR:
        query = query.where(LessonPlan.professor_id == current_user.id)
    result = await db.execute(query.order_by(LessonPlan.date.desc()))
    return result.scalars().all()


@router.post("/lesson-plans/", response_model=LessonPlanResponse, status_code=status.HTTP_201_CREATED)
async def create_lesson_plan(
    data: LessonPlanCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.PROFESSOR)),
):
    plan = LessonPlan(**data.model_dump(), professor_id=current_user.id)
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return plan


@router.put("/lesson-plans/{plan_id}", response_model=LessonPlanResponse)
async def update_lesson_plan(
    plan_id: UUID,
    data: LessonPlanUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.PROFESSOR)),
):
    result = await db.execute(select(LessonPlan).where(LessonPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plano de aula não encontrado")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(plan, key, value)
    await db.commit()
    await db.refresh(plan)
    return plan


@router.get("/lesson-plans/{plan_id}/details")
async def get_lesson_plan_details(
    plan_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.PROFESSOR)),
):
    # Fetch plan
    result = await db.execute(select(LessonPlan).where(LessonPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plano de aula não encontrado")
    
    # 1. Fetch Students (via Enrollment from matrix_subject_id)
    # We must fetch all students enrolled in the corresponding matrix_subject
    from sqlalchemy.orm import joinedload
    enrollments_result = await db.execute(
        select(Enrollment).options(joinedload(Enrollment.student)).where(
            Enrollment.matrix_subject_id == plan.matrix_subject_id,
            Enrollment.status == "active"
        )
    )
    enrollments = enrollments_result.scalars().all()
    students_map = {e.student_id: {"name": e.student.name, "enrollment_id": e.id} for e in enrollments if e.student}
    
    # 2. Fetch Attendances for this plan
    att_result = await db.execute(select(Attendance).where(Attendance.lesson_plan_id == plan_id))
    attendances_db = att_result.scalars().all()
    
    # 3. Fetch Grades for this plan (if activity)
    grades_db = []
    if plan.activity_type != "none":
        grades_result = await db.execute(select(Grade).where(Grade.lesson_plan_id == plan_id))
        grades_db = grades_result.scalars().all()

    # Format output for frontend matrix builder
    # The frontend needs flat lists or matrices.
    formatted_attendances = []
    for att in attendances_db:
        # Find student
        student_name = "Desconhecido"
        for s_id, data in students_map.items():
            if data["enrollment_id"] == att.enrollment_id:
                student_name = data["name"]
                break
        
        formatted_attendances.append({
            "id": att.id,
            "enrollment_id": att.enrollment_id,
            "student_name": student_name,
            "class_order_item": att.class_order_item,
            "present": att.present,
            "observation": att.observation
        })

    formatted_grades = []
    for g in grades_db:
        student_name = "Desconhecido"
        student_id = None
        for s_id, data in students_map.items():
            if data["enrollment_id"] == g.enrollment_id:
                student_name = data["name"]
                student_id = s_id
                break
        formatted_grades.append({
            "id": g.id,
            "enrollment_id": g.enrollment_id,
            "student_id": student_id,
            "student_name": student_name,
            "value": g.value,
            "observations": g.observations
        })

    return {
        "students": [{"id": k, "name": v["name"], "enrollment_id": v["enrollment_id"]} for k, v in students_map.items()],
        "attendance": formatted_attendances,
        "grades": formatted_grades
    }


# ========== MATERIALS ==========

@router.get("/materials/", response_model=list[MaterialResponse])
async def list_materials(
    matrix_subject_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Material)
    if matrix_subject_id:
        query = query.where(Material.matrix_subject_id == matrix_subject_id)
    result = await db.execute(query.order_by(Material.uploaded_at.desc()))
    return result.scalars().all()


@router.post("/materials/", response_model=MaterialResponse, status_code=status.HTTP_201_CREATED)
async def create_material(
    data: MaterialCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.PROFESSOR)),
):
    material = Material(**data.model_dump(), professor_id=current_user.id)
    db.add(material)
    await db.commit()
    await db.refresh(material)
    return material


# ========== ANNOUNCEMENTS ==========

@router.get("/announcements/", response_model=list[AnnouncementResponse])
async def list_announcements(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: Optional[UUID] = Depends(get_current_tenant_id),
):
    query = select(Announcement).where(Announcement.is_active == True)
    if tenant_id:
        query = query.where(Announcement.tenant_id == tenant_id)
    result = await db.execute(query.order_by(Announcement.pinned.desc(), Announcement.created_at.desc()))
    return result.scalars().all()


@router.post("/announcements/", response_model=AnnouncementResponse, status_code=status.HTTP_201_CREATED)
async def create_announcement(
    data: AnnouncementCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.PROFESSOR)),
    tenant_id: UUID = Depends(get_required_tenant_id),
):
    announcement = Announcement(
        **data.model_dump(),
        tenant_id=tenant_id,
        author_id=current_user.id,
    )
    db.add(announcement)
    await db.commit()
    await db.refresh(announcement)
    return announcement


@router.put("/announcements/{announcement_id}", response_model=AnnouncementResponse)
async def update_announcement(
    announcement_id: UUID,
    data: AnnouncementUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.PROFESSOR)),
):
    result = await db.execute(select(Announcement).where(Announcement.id == announcement_id))
    announcement = result.scalar_one_or_none()
    if not announcement:
        raise HTTPException(status_code=404, detail="Aviso não encontrado")
    for key, value in data.model_dump(exclude_unset=True).items():
        if key == "target":
            setattr(announcement, key, AnnouncementTarget(value))
        else:
            setattr(announcement, key, value)
    await db.commit()
    await db.refresh(announcement)
    return announcement


@router.delete("/announcements/{announcement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_announcement(
    announcement_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN)),
):
    result = await db.execute(select(Announcement).where(Announcement.id == announcement_id))
    announcement = result.scalar_one_or_none()
    if not announcement:
        raise HTTPException(status_code=404, detail="Aviso não encontrado")
    announcement.is_active = False
    await db.commit()
