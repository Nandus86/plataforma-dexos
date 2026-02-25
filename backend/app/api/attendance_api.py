"""
Attendance API Router - Mounted at /attendance
Provides CRUD for attendance records and external API integration.
"""
from uuid import UUID
from typing import Optional
from datetime import datetime, time, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User, UserRole
from app.models.academic import Attendance, Enrollment
from app.models.class_group import ClassGroupStudent, ClassSchedule
from app.auth.dependencies import get_current_user, require_role
from app.schemas.academic import AttendanceCreate, AttendanceResponse, AttendanceBulkCreate, AttendanceCheckin, AttendanceBiometricCheckin

router = APIRouter()


@router.get("/", response_model=list[AttendanceResponse])
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


@router.post("/", response_model=AttendanceResponse, status_code=status.HTTP_201_CREATED)
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


@router.put("/{attendance_id}", response_model=AttendanceResponse)
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


@router.post("/bulk", status_code=status.HTTP_201_CREATED)
async def bulk_create_attendance(
    data: AttendanceBulkCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.PROFESSOR)),
):
    """Bulk attendance for an entire class session."""
    created = []
    for record in data.records:
        # Find enrollment for this student
        enrollment_query = select(Enrollment).where(Enrollment.student_id == record.student_id)
        enrollment_result = await db.execute(enrollment_query)
        enrollment = enrollment_result.scalar_one_or_none()
        if not enrollment:
            continue

        attendance = Attendance(
            enrollment_id=enrollment.id,
            lesson_plan_id=data.lesson_plan_id,
            class_order_item=data.class_order_item,
            class_date=data.class_date,
            present=record.present,
            checkin_method="manual",
            observation=record.observation
        )
        db.add(attendance)
        created.append(attendance)

    await db.commit()
    return {"created": len(created)}


@router.post("/checkin", response_model=AttendanceResponse)
async def api_checkin(
    data: AttendanceCheckin,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.PROFESSOR)),
):
    """External API check-in endpoint for biometric/QR/third-party integrations."""
    # Find the student's enrollment
    enrollment_query = select(Enrollment).where(Enrollment.student_id == data.student_id)
    enrollment_result = await db.execute(enrollment_query)
    enrollment = enrollment_result.scalar_one_or_none()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Matrícula do estudante não encontrada")

    attendance = Attendance(
        enrollment_id=enrollment.id,
        class_date=datetime.utcnow(),
        present=True,
        checkin_method=data.checkin_method,
    )
    db.add(attendance)
    await db.commit()
    await db.refresh(attendance)
    return attendance


@router.post("/biometric", response_model=AttendanceResponse)
async def checkin_biometric(
    data: AttendanceBiometricCheckin,
    db: AsyncSession = Depends(get_db)
):
    """
    Biometric Hook for Machine-to-Machine Checkin.
    Finds the active LessonPlan automatically based on current time and ClassSchedules.
    Handles multiple consecutive classes (e.g. 1st and 2nd class) by checking the range
    from the start of the first to the end of the last.
    """
    import zoneinfo
    tz_sp = zoneinfo.ZoneInfo("America/Sao_Paulo")
    
    if data.timestamp:
        if data.timestamp.tzinfo is not None:
            checkin_time = data.timestamp.astimezone(tz_sp).replace(tzinfo=None)
        else:
            checkin_time = data.timestamp
    else:
        checkin_time = datetime.now(tz=tz_sp).replace(tzinfo=None)

    checkin_date = checkin_time.date()
    
    from app.models.class_group import ClassSchedule
    from functools import reduce

    # 1. Find the student by RA
    user_query = select(User).where(User.registration_number == data.registration_number)
    user_res = await db.execute(user_query)
    student = user_res.scalar_one_or_none()
    
    if not student:
        raise HTTPException(status_code=404, detail="Estudante não encontrado com este RA")

    # 2. Get active enrollments for this student
    enrollments_query = select(Enrollment).where(
        Enrollment.student_id == student.id,
        Enrollment.status == "active"
    )
    enrollments_res = await db.execute(enrollments_query)
    enrollments = enrollments_res.scalars().all()
    
    if not enrollments:
        raise HTTPException(status_code=404, detail="Estudante não possui matrículas ativas")

    enrollment_ids = [e.id for e in enrollments]

    # 3. Find ClassGroups the student is in
    cg_students_query = select(ClassGroupStudent).options(
        selectinload(ClassGroupStudent.class_group)
    ).where(ClassGroupStudent.enrollment_id.in_(enrollment_ids))
    cg_students_res = await db.execute(cg_students_query)
    cg_students = cg_students_res.scalars().all()
    
    if not cg_students:
        raise HTTPException(status_code=404, detail="Estudante não está vinculado a nenhuma turma")
        
    class_group_ids = [cgs.class_group_id for cgs in cg_students]
    academic_period_ids = list(set([cgs.class_group.academic_period_id for cgs in cg_students if cgs.class_group.academic_period_id]))

    # Find ClassGroupSubjects to match against LessonPlans
    from app.models.class_group import ClassGroupSubject
    cg_subjects_query = select(ClassGroupSubject).where(ClassGroupSubject.class_group_id.in_(class_group_ids))
    cg_subjects_res = await db.execute(cg_subjects_query)
    cg_subjects = cg_subjects_res.scalars().all()
    cg_subject_ids = [sub.id for sub in cg_subjects]

    if not cg_subject_ids:
        raise HTTPException(status_code=404, detail="A turma do estudante ainda não possui disciplinas associadas")

    # 4. Get active LessonPlans for TODAY for these subjects
    lp_query = select(LessonPlan).where(
        LessonPlan.class_group_subject_id.in_(cg_subject_ids),
        LessonPlan.date >= datetime.combine(checkin_date, time.min),
        LessonPlan.date <= datetime.combine(checkin_date, time.max)
    )
    lp_res = await db.execute(lp_query)
    lesson_plans = lp_res.scalars().all()
    
    if not lesson_plans:
        raise HTTPException(status_code=404, detail="Nenhuma aula (LessonPlan) planejada para o dia de hoje nas disciplinas deste aluno")

    # 5. Get ClassSchedules for the class groups the student is enrolled in
    schedule_query = select(ClassSchedule).where(ClassSchedule.class_group_id.in_(class_group_ids))
    schedule_res = await db.execute(schedule_query)
    schedules = schedule_res.scalars().all()
    
    # 6. Inference Loop: Find ALL colliding LessonPlans based on time
    colliding_plans = []
    
    TOLERANCE_MINUTES = 15
    
    for lp in lesson_plans:
        if not lp.class_orders:
            continue
            
        lp_cg_sub = next((s for s in cg_subjects if s.id == lp.class_group_subject_id), None)
        if not lp_cg_sub: continue
        
        target_cgs = next((cgs for cgs in cg_students if cgs.class_group_id == lp_cg_sub.class_group_id), None)
        if not target_cgs or not target_cgs.class_group.academic_period_id: continue
        
        target_enrollment = next((e for e in enrollments if e.id == target_cgs.enrollment_id), None)
        if not target_enrollment: continue
        
        period_schedules = [s for s in schedules if s.class_group_id == target_cgs.class_group_id and s.order in lp.class_orders]
        
        if not period_schedules:
            continue
            
        period_schedules.sort(key=lambda x: x.order)
        start_time = period_schedules[0].start_time
        end_time = period_schedules[-1].end_time
        
        start_dt = datetime.combine(checkin_date, start_time) - timedelta(minutes=TOLERANCE_MINUTES)
        end_dt = datetime.combine(checkin_date, end_time) + timedelta(minutes=TOLERANCE_MINUTES)
        
        if start_dt <= checkin_time <= end_dt:
            colliding_plans.append({
                "plan": lp,
                "enrollment_id": target_enrollment.id
            })

    if not colliding_plans:
        raise HTTPException(status_code=403, detail="Batida fora do horário de aula ou aula não encontrada na grade para a hora atual")

    # 7. Register or Update Attendance for each class order across ALL colliding plans
    from sqlalchemy import update
    
    records_updated = []
    
    for collision in colliding_plans:
        plan = collision["plan"]
        enrollment_id = collision["enrollment_id"]
        
        for order in plan.class_orders:
            existing_attendance_query = select(Attendance).where(
                Attendance.enrollment_id == enrollment_id,
                Attendance.lesson_plan_id == plan.id,
                Attendance.class_order_item == order
            )
            existing_res = await db.execute(existing_attendance_query)
            attendance = existing_res.scalar_one_or_none()
            
            if attendance:
                # Update existing 'absent' placeholder generated during Lesson Plan creation
                if attendance.present and attendance.checkin_method == data.checkin_method:
                    # If already present via biometric, skip it
                    continue
                    
                attendance.present = True
                attendance.checkin_method = data.checkin_method
                attendance.class_date = checkin_time
                records_updated.append(attendance)
            else:
                # Fallback if no placeholder existed
                attendance = Attendance(
                    enrollment_id=enrollment_id,
                    lesson_plan_id=plan.id,
                    class_order_item=order,
                    class_date=checkin_time,
                    present=True,
                    checkin_method=data.checkin_method,
                )
                db.add(attendance)
                records_updated.append(attendance)

    if not records_updated:
        raise HTTPException(status_code=400, detail="Presença desta aula já foi registrada completamente")

    await db.commit()
    
    if records_updated:
        await db.refresh(records_updated[0])
        return records_updated[0]
