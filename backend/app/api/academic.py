"""
Academic API - Enrollments, Grades, Attendance (with check-in via API)
"""
from uuid import UUID
from typing import Optional
from datetime import datetime, time
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.user import User, UserRole
from app.models.course import Course
from app.models.academic import Enrollment, Grade, Attendance
from app.models.academic_period import PeriodBreak
from app.models.content import LessonPlan
from app.models.class_group import ClassGroupStudent, ClassGroupStudentSubject, ClassGroup
from app.models.course import Subject, MatrixSubject, CurriculumMatrix
from app.schemas.academic import (
    EnrollmentCreate, EnrollmentUpdate, EnrollmentResponse,
    GradeCreate, GradeUpdate, GradeResponse,
    AttendanceCreate, AttendanceBulkCreate, AttendanceCheckin, AttendanceBiometricCheckin, AttendanceResponse,
    BoletimResponse, SubjectBoletim, GradeSummary
)
from app.auth.dependencies import get_current_user, require_role

router = APIRouter()


# ========== ENROLLMENTS ==========

@router.get("/enrollments/", response_model=list[EnrollmentResponse])
async def list_enrollments(
    student_id: Optional[UUID] = None,
    course_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Enrollment).options(
        selectinload(Enrollment.student),
        selectinload(Enrollment.course),
        selectinload(Enrollment.academic_period),
        selectinload(Enrollment.period_breaks),
    )
    if current_user.role == UserRole.ESTUDANTE:
        query = query.where(Enrollment.student_id == current_user.id)
    elif student_id:
        query = query.where(Enrollment.student_id == student_id)
    if course_id:
        query = query.where(Enrollment.course_id == course_id)
    result = await db.execute(query.order_by(Enrollment.created_at.desc()))
    enrollments = result.scalars().all()
    return [
        EnrollmentResponse(
            id=e.id, student_id=e.student_id, course_id=e.course_id,
            year=e.year, academic_period_id=e.academic_period_id,
            period_breaks=[{"id": pb.id, "name": pb.name} for pb in e.period_breaks],
            enrollment_code=e.enrollment_code,
            status=e.status.value if hasattr(e.status, 'value') else e.status,
            created_at=e.created_at,
            student_name=e.student.name if e.student else None,
            course_name=e.course.name if e.course else None,
            academic_period_name=e.academic_period.name if getattr(e, 'academic_period', None) else None,
        )
        for e in enrollments
    ]


@router.post("/enrollments/", response_model=EnrollmentResponse, status_code=status.HTTP_201_CREATED)
async def create_enrollment(
    data: EnrollmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN)),
):
    # Verify course exists
    result = await db.execute(select(Course).where(Course.id == data.course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Curso não encontrado")

    # Check for duplicate unique enrollment (Student + Course + Period)
    existing = await db.execute(
        select(Enrollment).where(
            Enrollment.student_id == data.student_id,
            Enrollment.course_id == data.course_id,
            Enrollment.academic_period_id == data.academic_period_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Aluno já tem uma matrícula neste curso/período. Atualize a existente.")

    # Fetch period breaks
    pbs_result = await db.execute(select(PeriodBreak).where(PeriodBreak.id.in_(data.period_break_ids)))
    period_breaks = pbs_result.scalars().all()
    if not period_breaks and data.period_break_ids:
        raise HTTPException(status_code=404, detail="Alguns períodos informados não foram encontrados.")

    # Load student and period to generate code
    from app.models.academic_period import AcademicPeriod
    student_result = await db.execute(select(User).where(User.id == data.student_id))
    student = student_result.scalar_one_or_none()
    
    period_result = await db.execute(select(AcademicPeriod).where(AcademicPeriod.id == data.academic_period_id))
    period = period_result.scalar_one_or_none()

    from app.core.registration import generate_enrollment_code
    
    enrollment_code = None
    if student and period and student.registration_number:
        enrollment_code = await generate_enrollment_code(db, student.registration_number, period.year)

    new_data = data.model_dump(exclude={'period_break_ids'})
    new_data['enrollment_code'] = enrollment_code
    enrollment = Enrollment(**new_data)
    enrollment.period_breaks = list(period_breaks)
    
    db.add(enrollment)
    await db.commit()
    await db.refresh(enrollment)
    await db.refresh(enrollment, ['academic_period', 'period_breaks'])

    # Load student name
    student_result = await db.execute(select(User).where(User.id == enrollment.student_id))
    student = student_result.scalar_one_or_none()

    return EnrollmentResponse(
        id=enrollment.id, student_id=enrollment.student_id, course_id=enrollment.course_id,
        year=enrollment.year, academic_period_id=enrollment.academic_period_id,
        period_breaks=[{"id": pb.id, "name": pb.name} for pb in enrollment.period_breaks],
        enrollment_code=enrollment.enrollment_code,
        status=enrollment.status.value if hasattr(enrollment.status, 'value') else enrollment.status,
        created_at=enrollment.created_at,
        student_name=student.name if student else None,
        course_name=course.name,
        academic_period_name=enrollment.academic_period.name if getattr(enrollment, 'academic_period', None) else None,
    )


@router.put("/enrollments/{enrollment_id}", response_model=EnrollmentResponse)
async def update_enrollment(
    enrollment_id: UUID,
    data: EnrollmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN)),
):
    result = await db.execute(select(Enrollment).where(Enrollment.id == enrollment_id))
    enrollment = result.scalar_one_or_none()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Matrícula não encontrada")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(enrollment, key, value)
    await db.commit()
    await db.refresh(enrollment)
    return enrollment



# ========== BOLETIM ==========

@router.get("/boletim/{enrollment_id}", response_model=BoletimResponse)
async def get_boletim(
    enrollment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 1. Load enrollment
    query = select(Enrollment).options(
        selectinload(Enrollment.student),
        selectinload(Enrollment.course),
        selectinload(Enrollment.academic_period),
    ).where(Enrollment.id == enrollment_id)
    result = await db.execute(query)
    enrollment = result.scalar_one_or_none()
    
    if not enrollment:
        raise HTTPException(status_code=404, detail="Matrícula não encontrada")
    
    if current_user.role == UserRole.ESTUDANTE and enrollment.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Acesso negado")

    # 2. Find subjects student is enrolled in through ClassGroupStudentSubject
    subjects_query = select(Subject, ClassGroupStudentSubject).join(
        ClassGroupStudentSubject, Subject.id == ClassGroupStudentSubject.subject_id
    ).where(
        ClassGroupStudentSubject.enrollment_id == enrollment.id,
        ClassGroupStudentSubject.is_active == True
    )
    subjects_result = await db.execute(subjects_query)
    enrolled_subjects = subjects_result.all()  # list of tuples (Subject, ClassGroupStudentSubject)

    subjects_response = []

    for subject, cg_student_subject in enrolled_subjects:
        matrix_subject_query = select(MatrixSubject).join(
            CurriculumMatrix, CurriculumMatrix.id == MatrixSubject.matrix_id
        ).where(
            MatrixSubject.subject_id == subject.id,
            CurriculumMatrix.course_id == enrollment.course_id
        )
        ms_res = await db.execute(matrix_subject_query)
        matrix_subject = ms_res.scalar_one_or_none()

        total_planned_classes = 0
        total_presences = 0
        grades = []

        if matrix_subject:
            # Get LessonPlans for this matrix_subject
            lp_query = select(LessonPlan).where(LessonPlan.matrix_subject_id == matrix_subject.id)
            lp_res = await db.execute(lp_query)
            lesson_plans = lp_res.scalars().all()
            
            lp_ids = []
            for lp in lesson_plans:
                lp_ids.append(lp.id)
                total_planned_classes += len(lp.class_orders) if lp.class_orders else 1
            
            if lp_ids:
                # Get Attendances
                att_query = select(Attendance).where(
                    Attendance.enrollment_id == enrollment.id,
                    Attendance.lesson_plan_id.in_(lp_ids),
                    Attendance.present == True
                )
                att_res = await db.execute(att_query)
                total_presences = len(att_res.scalars().all())

                # Get Grades
                g_query = select(Grade).where(
                    Grade.enrollment_id == enrollment.id,
                    Grade.lesson_plan_id.in_(lp_ids)
                )
                g_res = await db.execute(g_query)
                for g in g_res.scalars().all():
                    grades.append(GradeSummary(
                        id=g.id,
                        evaluation_name=g.evaluation_name,
                        value=g.value,
                        max_value=g.max_value,
                        date=g.date,
                        lesson_plan_id=g.lesson_plan_id,
                        observations=g.observations
                    ))
        
        # Calculate frequency
        freq = (total_presences / total_planned_classes * 100) if total_planned_classes > 0 else 100.0

        subjects_response.append(SubjectBoletim(
            subject_id=subject.id,
            subject_name=subject.name,
            total_planned_classes=total_planned_classes,
            total_presences=total_presences,
            frequency_percentage=round(freq, 2),
            grades=grades
        ))
        
    return BoletimResponse(
        student_id=enrollment.student_id,
        student_name=enrollment.student.name if enrollment.student else "Desconhecido",
        enrollment_id=enrollment.id,
        course_id=enrollment.course_id,
        course_name=enrollment.course.name if enrollment.course else "Curso Desconhecido",
        academic_period_id=enrollment.academic_period_id,
        academic_period_name=enrollment.academic_period.name if enrollment.academic_period else "Período Desconhecido",
        subjects=subjects_response
    )

# ========== GRADES ==========

@router.get("/grades/", response_model=list[GradeResponse])
async def list_grades(
    enrollment_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Grade)
    if current_user.role == UserRole.ESTUDANTE:
        # Student can only see own grades
        student_enrollments = select(Enrollment.id).where(Enrollment.student_id == current_user.id)
        query = query.where(Grade.enrollment_id.in_(student_enrollments))
    elif enrollment_id:
        query = query.where(Grade.enrollment_id == enrollment_id)
    result = await db.execute(query.order_by(Grade.created_at.desc()))
    return result.scalars().all()


@router.post("/grades/", response_model=GradeResponse, status_code=status.HTTP_201_CREATED)
async def create_grade(
    data: GradeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.PROFESSOR)),
):
    """Create a grade (professor or admin)"""
    grade = Grade(**data.model_dump())
    db.add(grade)
    await db.commit()
    await db.refresh(grade)
    return grade


@router.put("/grades/{grade_id}", response_model=GradeResponse)
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


@router.delete("/grades/{grade_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_grade(
    grade_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.PROFESSOR)),
):
    result = await db.execute(select(Grade).where(Grade.id == grade_id))
    grade = result.scalar_one_or_none()
    if not grade:
        raise HTTPException(status_code=404, detail="Nota não encontrada")
    await db.delete(grade)
    await db.commit()


# ========== ATTENDANCE ==========

@router.get("/attendance/", response_model=list[AttendanceResponse])
async def list_attendance(
    enrollment_id: Optional[UUID] = None,
    lesson_plan_id: Optional[UUID] = None,
    class_order_item: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Attendance)
    if current_user.role == UserRole.ESTUDANTE:
        student_enrollments = select(Enrollment.id).where(Enrollment.student_id == current_user.id)
        query = query.where(Attendance.enrollment_id.in_(student_enrollments))
    elif enrollment_id:
        query = query.where(Attendance.enrollment_id == enrollment_id)
    
    if lesson_plan_id:
        query = query.where(Attendance.lesson_plan_id == lesson_plan_id)
    if class_order_item is not None:
        query = query.where(Attendance.class_order_item == class_order_item)

    result = await db.execute(query.order_by(Attendance.class_date.desc()))
    return result.scalars().all()


@router.post("/attendance/", response_model=AttendanceResponse, status_code=status.HTTP_201_CREATED)
async def create_attendance(
    data: AttendanceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.PROFESSOR)),
):
    attendance = Attendance(**data.model_dump())
    db.add(attendance)
    await db.commit()
    await db.refresh(attendance)
    return attendance


@router.put("/attendance/{attendance_id}", response_model=AttendanceResponse)
async def update_attendance(
    attendance_id: UUID,
    data: AttendanceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.PROFESSOR)),
):
    result = await db.execute(select(Attendance).where(Attendance.id == attendance_id))
    attendance = result.scalar_one_or_none()
    if not attendance:
        raise HTTPException(status_code=404, detail="Registro de frequência não encontrado")
    
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(attendance, key, value)
        
    await db.commit()
    await db.refresh(attendance)
    return attendance


@router.post("/attendance/bulk", status_code=status.HTTP_201_CREATED)
async def bulk_create_attendance(
    data: AttendanceBulkCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.PROFESSOR)),
):
    """Bulk create attendance records for a class session"""
    created = []
    for record in data.records:
        # Find enrollment for this student in this subject
        result = await db.execute(
            select(Enrollment).where(
                Enrollment.student_id == record.student_id,
                Enrollment.matrix_subject_id == data.matrix_subject_id,
            )
        )
        enrollment = result.scalar_one_or_none()
        if enrollment:
            attendance = Attendance(
                enrollment_id=enrollment.id,
                lesson_plan_id=data.lesson_plan_id,
                class_order_item=data.class_order_item,
                class_date=data.class_date,
                present=record.present,
                checkin_method="manual",
                observation=record.observation,
            )
            db.add(attendance)
            created.append(attendance)

    await db.commit()
    return {"created": len(created)}


@router.post("/attendance/checkin", response_model=AttendanceResponse)
async def checkin(
    data: AttendanceCheckin,
    db: AsyncSession = Depends(get_db),
):
    """API-based check-in endpoint. Agnostic to method (manual, biometric, QR, NFC)."""
    # Find active enrollment
    result = await db.execute(
        select(Enrollment).where(
            Enrollment.student_id == data.student_id,
            Enrollment.matrix_subject_id == data.matrix_subject_id,
            Enrollment.status == "active",
        )
    )
    enrollment = result.scalar_one_or_none()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Matrícula ativa não encontrada para este estudante nesta disciplina")

    attendance = Attendance(
        enrollment_id=enrollment.id,
        class_date=datetime.utcnow(),
        present=True,
        checkin_method=data.checkin_method,
    )
    db.add(attendance)
    await db.commit()
    return attendance

