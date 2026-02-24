"""
Export API - Data export for backup (CSV)
"""
import csv
import io
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.user import User, UserRole
from app.models.course import Course, Subject
from app.models.academic import Enrollment, Grade, Attendance
from app.auth.dependencies import require_role, get_current_tenant_id

router = APIRouter()


def _make_csv_response(rows: list[list[str]], headers: list[str], filename: str) -> StreamingResponse:
    """Create a CSV StreamingResponse"""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(rows)
    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/students")
async def export_students(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.COORDENACAO)),
    tenant_id: Optional[UUID] = Depends(get_current_tenant_id),
):
    """Export all students as CSV"""
    query = select(User).where(User.role == UserRole.ESTUDANTE)
    if tenant_id:
        query = query.where(User.tenant_id == tenant_id)
    result = await db.execute(query.order_by(User.name))
    users = result.scalars().all()

    headers = ["Nome", "Email", "Matrícula", "Telefone", "Status", "Criado em"]
    rows = [
        [
            u.name,
            u.email,
            u.registration_number or "",
            u.phone or "",
            "Ativo" if u.is_active else "Inativo",
            u.created_at.strftime("%d/%m/%Y %H:%M") if u.created_at else "",
        ]
        for u in users
    ]
    return _make_csv_response(rows, headers, "estudantes.csv")


@router.get("/grades")
async def export_grades(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.COORDENACAO)),
):
    """Export all grades as CSV"""
    query = (
        select(Grade, Enrollment, User)
        .join(Enrollment, Grade.enrollment_id == Enrollment.id)
        .join(User, Enrollment.student_id == User.id)
        .order_by(User.name, Grade.evaluation_name)
    )
    result = await db.execute(query)
    rows_data = result.all()

    headers = ["Aluno", "Matrícula", "Avaliação", "Nota", "Nota Máxima", "Data", "Observações"]
    rows = [
        [
            user.name,
            user.registration_number or "",
            grade.evaluation_name,
            str(grade.value),
            str(grade.max_value),
            grade.date.strftime("%d/%m/%Y") if grade.date else "",
            grade.observations or "",
        ]
        for grade, enrollment, user in rows_data
    ]
    return _make_csv_response(rows, headers, "notas.csv")


@router.get("/attendance")
async def export_attendance(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.COORDENACAO)),
):
    """Export all attendance records as CSV"""
    query = (
        select(Attendance, Enrollment, User)
        .join(Enrollment, Attendance.enrollment_id == Enrollment.id)
        .join(User, Enrollment.student_id == User.id)
        .order_by(User.name, Attendance.class_date)
    )
    result = await db.execute(query)
    rows_data = result.all()

    headers = ["Aluno", "Matrícula", "Data da Aula", "Presente", "Método", "Observação"]
    rows = [
        [
            user.name,
            user.registration_number or "",
            att.class_date.strftime("%d/%m/%Y %H:%M") if att.class_date else "",
            "Sim" if att.present else "Não",
            att.checkin_method or "",
            att.observation or "",
        ]
        for att, enrollment, user in rows_data
    ]
    return _make_csv_response(rows, headers, "frequencia.csv")
