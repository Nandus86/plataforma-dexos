from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID
from datetime import datetime
from typing import List, Optional

from app.database import get_db
from app.models.user import User, UserRole
from app.models.academic import Enrollment, Grade, Attendance
from app.models.occurrence import Occurrence
from app.models.intervention import PedagogicalIntervention, InterventionStatus
from app.auth.dependencies import require_role, get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/coordination", tags=["Coordination"])

class InterventionCreate(BaseModel):
    student_id: UUID
    title: str
    description: str
    action_plan: Optional[str] = None

class InterventionUpdate(BaseModel):
    status: InterventionStatus
    action_plan: Optional[str] = None

@router.get("/students/{student_id}/dossier")
async def get_student_dossier(
    student_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.COORDENACAO, UserRole.ADMIN))
):
    # Fetch student
    res = await db.execute(select(User).where(User.id == student_id, User.tenant_id == current_user.tenant_id))
    student = res.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Fetch Enrollments
    res = await db.execute(select(Enrollment).where(Enrollment.student_id == student_id))
    enrollments = res.scalars().all()
    enrollment_ids = [e.id for e in enrollments]

    grades = []
    attendances = []
    if enrollment_ids:
        res = await db.execute(select(Grade).where(Grade.enrollment_id.in_(enrollment_ids)))
        grades = res.scalars().all()
        
        res = await db.execute(select(Attendance).where(Attendance.enrollment_id.in_(enrollment_ids)))
        attendances = res.scalars().all()

    # Fetch Occurrences
    res = await db.execute(select(Occurrence).where(Occurrence.student_id == student_id))
    occurrences = res.scalars().all()

    # Fetch Interventions
    res = await db.execute(select(PedagogicalIntervention).where(PedagogicalIntervention.student_id == student_id))
    interventions = res.scalars().all()

    return {
        "student": {
            "id": student.id,
            "name": student.name,
            "email": student.email,
        },
        "enrollments_count": len(enrollments),
        "grades": [{"id": g.id, "value": g.value, "max_value": g.max_value, "evaluation_name": g.evaluation_name, "date": g.date, "enrollment_id": g.enrollment_id} for g in grades],
        "attendances": [{"id": a.id, "present": a.present, "class_date": a.class_date, "observation": a.observation, "enrollment_id": a.enrollment_id} for a in attendances],
        "occurrences": [{"id": o.id, "type": o.type, "title": o.title, "date": o.date, "description": o.description} for o in occurrences],
        "interventions": [{"id": i.id, "title": i.title, "status": i.status, "description": i.description, "action_plan": i.action_plan, "created_at": i.created_at} for i in interventions]
    }


@router.post("/interventions")
async def create_intervention(
    data: InterventionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.COORDENACAO, UserRole.ADMIN))
):
    intervention = PedagogicalIntervention(
        tenant_id=current_user.tenant_id,
        student_id=data.student_id,
        coordinator_id=current_user.id,
        title=data.title,
        description=data.description,
        action_plan=data.action_plan,
        status=InterventionStatus.OPEN
    )
    db.add(intervention)
    await db.commit()
    await db.refresh(intervention)
    return intervention


@router.get("/interventions")
async def list_interventions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.COORDENACAO, UserRole.ADMIN))
):
    res = await db.execute(
        select(PedagogicalIntervention)
        .where(PedagogicalIntervention.tenant_id == current_user.tenant_id)
        .order_by(PedagogicalIntervention.created_at.desc())
    )
    interventions = res.scalars().all()
    
    # We should return student info too
    student_ids = list(set([i.student_id for i in interventions]))
    students = {}
    if student_ids:
        res = await db.execute(select(User).where(User.id.in_(student_ids)))
        for s in res.scalars().all():
            students[s.id] = s.name

    return [
        {
            "id": i.id,
            "student_id": i.student_id,
            "student_name": students.get(i.student_id, "Desconhecido"),
            "title": i.title,
            "status": i.status,
            "created_at": i.created_at
        } for i in interventions
    ]


@router.put("/interventions/{intervention_id}")
async def update_intervention(
    intervention_id: UUID,
    data: InterventionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.SUPERADMIN, UserRole.COORDENACAO, UserRole.ADMIN]))
):
    res = await db.execute(select(PedagogicalIntervention).where(PedagogicalIntervention.id == intervention_id, PedagogicalIntervention.tenant_id == current_user.tenant_id))
    intervention = res.scalar_one_or_none()
    if not intervention:
        raise HTTPException(status_code=404, detail="Intervention not found")

    intervention.status = data.status
    if data.action_plan is not None:
        intervention.action_plan = data.action_plan
    if data.status == InterventionStatus.RESOLVED:
        intervention.resolved_at = datetime.utcnow()

    await db.commit()
    return {"detail": "Intervention updated"}


@router.get("/analytics")
async def get_analytics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.SUPERADMIN, UserRole.COORDENACAO, UserRole.ADMIN]))
):
    # Dummy analytics for trend graphs, real implementation would aggregate grades by period.
    # For now, we will aggregate occurrences by type to build the pie chart.
    res = await db.execute(
        select(Occurrence.type, func.count(Occurrence.id))
        .where(Occurrence.tenant_id == current_user.tenant_id)
        .group_by(Occurrence.type)
    )
    occurrences_stats = res.all()
    
    # Trend for average grades per subject (mock structure for now, or simple query)
    res = await db.execute(
        select(func.avg(Grade.value))
        .where(Grade.tenant_id == current_user.tenant_id)
    )
    general_average = res.scalar_one_or_none() or 0

    return {
        "occurrences_distribution": [{"type": row[0], "count": row[1]} for row in occurrences_stats],
        "general_average": round(float(general_average), 2),
        # You can add more complex aggregates over time here
    }
