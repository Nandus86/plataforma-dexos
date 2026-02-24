"""
Dashboard API - Statistics and Pedagogical Reports
"""
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case, and_

from app.database import get_db
from app.models.user import User, UserRole
from app.models.course import Course, Subject, CurriculumMatrix, MatrixSubject
from app.models.class_group import ClassGroup, ClassGroupSubject, ClassGroupSubjectProfessor, ClassGroupStudentSubject
from app.models.academic import Enrollment, Grade, Attendance, EnrollmentStatus
from app.models.content import LessonPlan, Material
from app.models.occurrence import Occurrence
from app.auth.dependencies import get_current_user, require_role, get_current_tenant_id

router = APIRouter()


@router.get("/stats")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: Optional[UUID] = Depends(get_current_tenant_id),
):
    """Get dashboard statistics based on user role"""
    role = current_user.role

    if role in (UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.COORDENACAO):
        # Count students
        q_students = select(func.count(User.id)).where(User.role == UserRole.ESTUDANTE)
        if tenant_id:
            q_students = q_students.where(User.tenant_id == tenant_id)
        total_students = (await db.execute(q_students)).scalar() or 0

        # Count professors
        q_profs = select(func.count(User.id)).where(User.role == UserRole.PROFESSOR)
        if tenant_id:
            q_profs = q_profs.where(User.tenant_id == tenant_id)
        total_professors = (await db.execute(q_profs)).scalar() or 0

        # Count courses
        q_courses = select(func.count(Course.id))
        if tenant_id:
            q_courses = q_courses.where(Course.tenant_id == tenant_id)
        total_courses = (await db.execute(q_courses)).scalar() or 0

        # Count active enrollments
        total_enrollments = (await db.execute(
            select(func.count(Enrollment.id)).where(Enrollment.status == EnrollmentStatus.ACTIVE)
        )).scalar() or 0

        # Count subjects
        q_subjects = select(func.count(Subject.id))
        if tenant_id:
            q_subjects = q_subjects.where(Subject.tenant_id == tenant_id)
        total_subjects = (await db.execute(q_subjects)).scalar() or 0

        # Count lesson plans and materials (for all admin roles)
        total_lesson_plans = (await db.execute(
            select(func.count(LessonPlan.id))
        )).scalar() or 0
        total_materials = (await db.execute(
            select(func.count(Material.id))
        )).scalar() or 0

        return {
            "total_students": total_students,
            "total_professors": total_professors,
            "total_courses": total_courses,
            "total_enrollments": total_enrollments,
            "total_subjects": total_subjects,
            "total_lesson_plans": total_lesson_plans,
            "total_materials": total_materials,
        }

    elif role == UserRole.PROFESSOR:
        # Count subjects taught (Active ClassGroups)
        q_subjects = (
            select(func.count(func.distinct(ClassGroupSubject.subject_id)))
            .join(ClassGroupSubjectProfessor, ClassGroupSubjectProfessor.class_group_subject_id == ClassGroupSubject.id)
            .join(ClassGroup, ClassGroup.id == ClassGroupSubject.class_group_id)
            .where(
                ClassGroupSubjectProfessor.professor_id == current_user.id,
                ClassGroup.is_active == True
            )
        )
        total_subjects = (await db.execute(q_subjects)).scalar() or 0

        # Count enrollments in my subjects
        q_students = (
             select(func.count(func.distinct(ClassGroupStudentSubject.enrollment_id)))
             .join(ClassGroupSubject, 
                 and_(
                     ClassGroupSubject.class_group_id == ClassGroupStudentSubject.class_group_id,
                     ClassGroupSubject.subject_id == ClassGroupStudentSubject.subject_id
                 )
             )
             .join(ClassGroupSubjectProfessor, ClassGroupSubjectProfessor.class_group_subject_id == ClassGroupSubject.id)
             .join(ClassGroup, ClassGroup.id == ClassGroupSubject.class_group_id)
             .where(
                 ClassGroupSubjectProfessor.professor_id == current_user.id,
                 ClassGroupStudentSubject.is_active == True,
                 ClassGroup.is_active == True
             )
        )
        total_students = (await db.execute(q_students)).scalar() or 0

        # Count lesson plans
        total_lesson_plans = (await db.execute(
            select(func.count(LessonPlan.id)).where(LessonPlan.professor_id == current_user.id)
        )).scalar() or 0

        # Count materials
        total_materials = (await db.execute(
            select(func.count(Material.id)).where(Material.professor_id == current_user.id)
        )).scalar() or 0

        return {
            "total_subjects": total_subjects,
            "total_students": total_students,
            "total_lesson_plans": total_lesson_plans,
            "total_materials": total_materials,
        }

    else:
        # Aluno
        total_enrollments = (await db.execute(
            select(func.count(Enrollment.id)).where(
                and_(
                    Enrollment.student_id == current_user.id,
                    Enrollment.status == EnrollmentStatus.ACTIVE,
                )
            )
        )).scalar() or 0

        total_grades = (await db.execute(
            select(func.count(Grade.id)).join(
                Enrollment, Grade.enrollment_id == Enrollment.id
            ).where(Enrollment.student_id == current_user.id)
        )).scalar() or 0

        # Average grade
        avg_grade = (await db.execute(
            select(func.avg(Grade.value)).join(
                Enrollment, Grade.enrollment_id == Enrollment.id
            ).where(Enrollment.student_id == current_user.id)
        )).scalar()

        # Attendance percentage
        total_classes = (await db.execute(
            select(func.count(Attendance.id)).join(
                Enrollment, Attendance.enrollment_id == Enrollment.id
            ).where(Enrollment.student_id == current_user.id)
        )).scalar() or 0
        present_classes = (await db.execute(
            select(func.count(Attendance.id)).join(
                Enrollment, Attendance.enrollment_id == Enrollment.id
            ).where(
                and_(
                    Enrollment.student_id == current_user.id,
                    Attendance.present == True,
                )
            )
        )).scalar() or 0
        attendance_pct = round((present_classes / total_classes * 100), 1) if total_classes > 0 else 0

        return {
            "total_enrollments": total_enrollments,
            "total_grades": total_grades,
            "average_grade": round(avg_grade, 2) if avg_grade else 0,
            "attendance_percentage": attendance_pct,
        }


# ========== PEDAGOGICAL REPORTS (Coordenação / Admin) ==========

@router.get("/reports/low-performance")
async def report_low_performance(
    threshold: float = Query(default=6.0, description="Nota mínima de aprovação"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.COORDENACAO)),
):
    """Students with average grade below threshold"""
    query = (
        select(
            User.id.label("student_id"),
            User.name.label("student_name"),
            User.registration_number,
            func.avg(Grade.value).label("average_grade"),
            func.count(Grade.id).label("total_evaluations"),
        )
        .join(Enrollment, Enrollment.student_id == User.id)
        .join(Grade, Grade.enrollment_id == Enrollment.id)
        .where(Enrollment.status == EnrollmentStatus.ACTIVE)
        .group_by(User.id, User.name, User.registration_number)
        .having(func.avg(Grade.value) < threshold)
        .order_by(func.avg(Grade.value))
    )
    result = await db.execute(query)
    rows = result.all()
    return [
        {
            "student_id": str(r.student_id),
            "student_name": r.student_name,
            "registration_number": r.registration_number,
            "average_grade": round(r.average_grade, 2),
            "total_evaluations": r.total_evaluations,
        }
        for r in rows
    ]


@router.get("/reports/low-attendance")
async def report_low_attendance(
    threshold: float = Query(default=75.0, description="% mínima de frequência"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.COORDENACAO)),
):
    """Students with attendance percentage below threshold"""
    query = (
        select(
            User.id.label("student_id"),
            User.name.label("student_name"),
            User.registration_number,
            func.count(Attendance.id).label("total_classes"),
            func.sum(case((Attendance.present == True, 1), else_=0)).label("present_classes"),
        )
        .join(Enrollment, Enrollment.student_id == User.id)
        .join(Attendance, Attendance.enrollment_id == Enrollment.id)
        .where(Enrollment.status == EnrollmentStatus.ACTIVE)
        .group_by(User.id, User.name, User.registration_number)
        .order_by(func.sum(case((Attendance.present == True, 1), else_=0)) * 100.0 / func.count(Attendance.id))
    )
    result = await db.execute(query)
    rows = result.all()

    return [
        {
            "student_id": str(r.student_id),
            "student_name": r.student_name,
            "registration_number": r.registration_number,
            "total_classes": r.total_classes,
            "present_classes": r.present_classes,
            "attendance_percentage": round(r.present_classes / r.total_classes * 100, 1) if r.total_classes > 0 else 0,
        }
        for r in rows
        if r.total_classes > 0 and (r.present_classes / r.total_classes * 100) < threshold
    ]


@router.get("/reports/critical-subjects")
async def report_critical_subjects(
    grade_threshold: float = Query(default=6.0, description="Nota mínima de aprovação"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.COORDENACAO)),
):
    """Subjects with high failure/low-attendance rates"""
    # Get all subjects that have grades via lesson_plans
    query = (
        select(
            Subject.id.label("subject_id"),
            Subject.name.label("subject_name"),
            Subject.code.label("subject_code"),
            func.count(func.distinct(Grade.enrollment_id)).label("total_enrollments"),
            func.avg(Grade.value).label("average_grade"),
            func.count(Grade.id).label("total_grades"),
            func.sum(case((Grade.value < grade_threshold, 1), else_=0)).label("failed_count"),
        )
        .join(MatrixSubject, MatrixSubject.subject_id == Subject.id)
        .join(LessonPlan, LessonPlan.matrix_subject_id == MatrixSubject.id)
        .join(Grade, Grade.lesson_plan_id == LessonPlan.id)
        .group_by(Subject.id, Subject.name, Subject.code)
        .having(func.count(Grade.id) > 0)
        .order_by(func.avg(Grade.value))
    )
    result = await db.execute(query)
    rows = result.all()

    return [
        {
            "subject_id": str(r.subject_id),
            "subject_name": r.subject_name,
            "subject_code": r.subject_code,
            "total_enrollments": r.total_enrollments,
            "average_grade": round(r.average_grade, 2) if r.average_grade else 0,
            "failure_rate": round(r.failed_count / r.total_enrollments * 100, 1) if r.total_enrollments > 0 else 0,
        }
        for r in rows
    ]


@router.get("/reports/professor-activity")
async def report_professor_activity(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.COORDENACAO)),
):
    """Professor activity: lesson plans and materials by professor"""
    query = (
        select(
            User.id.label("professor_id"),
            User.name.label("professor_name"),
            func.count(func.distinct(MatrixSubject.id)).label("subjects_count"),
            func.count(func.distinct(LessonPlan.id)).label("lesson_plans_count"),
            func.count(func.distinct(Material.id)).label("materials_count"),
        )
        .outerjoin(MatrixSubject, MatrixSubject.professor_id == User.id)
        .outerjoin(LessonPlan, LessonPlan.professor_id == User.id)
        .outerjoin(Material, Material.professor_id == User.id)
        .where(User.role == UserRole.PROFESSOR)
        .group_by(User.id, User.name)
        .order_by(User.name)
    )
    result = await db.execute(query)
    rows = result.all()

    return [
        {
            "professor_id": str(r.professor_id),
            "professor_name": r.professor_name,
            "subjects_count": r.subjects_count,
            "lesson_plans_count": r.lesson_plans_count,
            "materials_count": r.materials_count,
        }
        for r in rows
    ]


@router.get("/reports/recent-occurrences")
async def report_recent_occurrences(
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.COORDENACAO)),
    tenant_id: Optional[UUID] = Depends(get_current_tenant_id),
):
    """Recent occurrences (warnings, praises, etc.)"""
    from sqlalchemy.orm import aliased
    Student = aliased(User)
    Author = aliased(User)

    query = (
        select(
            Occurrence.id,
            Occurrence.type,
            Occurrence.title,
            Occurrence.description,
            Occurrence.date,
            Occurrence.parent_notified,
            Student.name.label("student_name"),
            Author.name.label("author_name"),
        )
        .join(Student, Student.id == Occurrence.student_id)
        .join(Author, Author.id == Occurrence.author_id)
    )
    if tenant_id:
        query = query.where(Occurrence.tenant_id == tenant_id)

    query = query.order_by(Occurrence.created_at.desc()).limit(limit)
    result = await db.execute(query)
    rows = result.all()

    type_labels = {
        "praise": "Elogio",
        "warning": "Advertência",
        "complaint": "Reclamação",
        "observation": "Observação",
    }

    return [
        {
            "id": str(r.id),
            "type": r.type.value if hasattr(r.type, 'value') else r.type,
            "type_label": type_labels.get(r.type.value if hasattr(r.type, 'value') else r.type, r.type),
            "title": r.title,
            "description": r.description,
            "date": r.date.strftime("%d/%m/%Y") if r.date else "",
            "student_name": r.student_name,
            "author_name": r.author_name,
            "parent_notified": r.parent_notified,
        }
        for r in rows
    ]
