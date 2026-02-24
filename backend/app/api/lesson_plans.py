
from uuid import UUID
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, delete
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.user import User, UserRole
from app.models.content import LessonPlan, ActivityType
from app.models.academic import Attendance, Grade, EnrollmentStatus
from app.models.academic_period import AcademicPeriod
from app.models.class_group import ClassGroup, ClassGroupSubject, ClassGroupStudent
from app.schemas.lesson_plan import LessonPlanCreate, LessonPlanUpdate, LessonPlanResponse, LessonPlanDetailsResponse
from app.auth.dependencies import get_current_user, require_role
from app.models.academic import Enrollment, EnrollmentStatus

router = APIRouter()

@router.post("/", response_model=LessonPlanResponse, status_code=status.HTTP_201_CREATED)
async def create_lesson_plan(
    data: LessonPlanCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.PROFESSOR, UserRole.ADMIN, UserRole.SUPERADMIN)),
):
    """
    Create a Lesson Plan.
    - Validates if date is within Academic Period of the Class Group.
    - Auto-generates Attendance records (default Not Present or Present? Let's use Present=False initially, user marks presence).
    - Auto-generates Grade records if ActivityType != NONE.
    """
    # 1. Validate ClassGroupSubject relationship
    if not data.class_group_subject_id:
        raise HTTPException(status_code=400, detail="É necessário vincular a uma disciplina de turma.")

    result = await db.execute(
        select(ClassGroupSubject)
        .options(selectinload(ClassGroupSubject.class_group).selectinload(ClassGroup.academic_period))
        .where(ClassGroupSubject.id == data.class_group_subject_id)
    )
    cg_subject = result.scalar_one_or_none()
    if not cg_subject:
        raise HTTPException(status_code=404, detail="Disciplina de turma não encontrada.")
    
    class_group = cg_subject.class_group
    academic_period = class_group.academic_period

    # 2. Validate Academic Period
    # If ClassGroup has specific break, maybe validate that too?
    # For now, just check master period dates.
    if academic_period:
        # Check date range
        # Convert datetime to date for comparison if needed
        plan_date = data.date.date()
        if plan_date < academic_period.start_date or plan_date > academic_period.end_date:
             raise HTTPException(status_code=400, detail=f"A data do plano de aula deve estar dentro do período letivo ({academic_period.start_date} - {academic_period.end_date})")

             raise HTTPException(status_code=400, detail=f"A data do plano de aula deve estar dentro do período letivo ({academic_period.start_date} - {academic_period.end_date})")

    # Ensure date is naive UTC (DB expects naive)
    if data.date.tzinfo is not None:
        import datetime as dt
        # Convert to UTC then strip tzinfo
        data.date = data.date.astimezone(dt.timezone.utc).replace(tzinfo=None)

    # 3. Resolve matrix_subject_id if missing
    if not data.matrix_subject_id:
        # Strategy: ClassGroupSubject -> Subject -> MatrixSubject (linked to Course/Matrix)
        # However, ClassGroupSubject links to a Subject. The Subject might be part of multiple Matrices.
        # We need the Matrix active for this Class Group's Course and Year/Semester?
        # A simpler approach: The Request Body SHOULD preferably allow frontend to send it if known.
        # If not, we try to find ONE MatrixSubject for this Subject in the Course's active Matrix.
        
        # Helper query to find MatrixSubject
        # We know ClassGroup -> Course.
        # We know ClassGroupSubject -> Subject.
        # We need MatrixSubject where matrix.course_id = course.id AND subject_id = subject.id
        # And ideally matrix is active or matches the class group year?
        # Let's pick the most recent active matrix for the course.
        
        from app.models.course import MatrixSubject, CurriculumMatrix
        
        stmt = (
            select(MatrixSubject)
            .join(CurriculumMatrix)
            .where(
                CurriculumMatrix.course_id == class_group.course_id,
                CurriculumMatrix.is_active == True,
                MatrixSubject.subject_id == cg_subject.subject_id
            )
            .order_by(CurriculumMatrix.year.desc())
            .limit(1)
        )
        result_ms = await db.execute(stmt)
        matrix_subject = result_ms.scalar_one_or_none()
        
        if not matrix_subject:
             # Fallback: try any matrix for this course/subject
             stmt_fallback = (
                select(MatrixSubject)
                .join(CurriculumMatrix)
                .where(
                    CurriculumMatrix.course_id == class_group.course_id,
                    MatrixSubject.subject_id == cg_subject.subject_id
                )
                .order_by(CurriculumMatrix.year.desc())
                .limit(1)
            )
             result_fallback = await db.execute(stmt_fallback)
             matrix_subject = result_fallback.scalar_one_or_none()

        if not matrix_subject:
            # Auto-create matrix and matrix_subject if missing
            from datetime import datetime
            
            stmt_matrix = select(CurriculumMatrix).where(CurriculumMatrix.course_id == class_group.course_id).order_by(CurriculumMatrix.year.desc()).limit(1)
            res_mx = await db.execute(stmt_matrix)
            matrix = res_mx.scalar_one_or_none()
            
            if not matrix:
                matrix = CurriculumMatrix(
                    course_id=class_group.course_id,
                    name=f"Matriz Base",
                    year=datetime.now().year,
                    is_active=True
                )
                db.add(matrix)
                await db.flush()
                
            matrix_subject = MatrixSubject(
                matrix_id=matrix.id,
                subject_id=cg_subject.subject_id,
                semester=1
            )
            db.add(matrix_subject)
            await db.flush()

        data.matrix_subject_id = matrix_subject.id

    # 4. Create LessonPlan
    lesson_plan = LessonPlan(
        **data.model_dump(),
        professor_id=current_user.id
    )
    db.add(lesson_plan)
    await db.flush() # Get ID

    # 4. Auto-generate Attendance
    # Get all active students in this Class Group
    students_res = await db.execute(
        select(ClassGroupStudent)
        .where(ClassGroupStudent.class_group_id == class_group.id)
    )
    group_students = students_res.scalars().all()

    for gs in group_students:
        # gs.enrollment_id is an FK to a real Enrollment. We just verify it's ACTIVE.
        enrollment_res = await db.execute(
            select(Enrollment).where(
                Enrollment.id == gs.enrollment_id,
                Enrollment.status == EnrollmentStatus.ACTIVE
            )
        )
        enrollment = enrollment_res.scalar_one_or_none()
        
        if enrollment:
            # Create Attendance
            for order in data.class_orders:
                att = Attendance(
                    enrollment_id=enrollment.id,
                    lesson_plan_id=lesson_plan.id,
                    class_order_item=order,
                    class_date=data.date,
                    present=False, # Default to absent/unchecked
                    checkin_method="manual"
                )
                db.add(att)
            
            # 5. Auto-generate Grade (if applicable)
            if data.activity_type != ActivityType.none:
                grade = Grade(
                    enrollment_id=enrollment.id,
                    lesson_plan_id=lesson_plan.id,
                    evaluation_name=f"{data.activity_type.value.title()}: {data.topic}",
                    value=0.0, # Initial grade
                    max_value=data.max_score or 10.0,
                    date=data.date
                )
                db.add(grade)
    
    await db.commit()
    await db.refresh(lesson_plan)
    return lesson_plan


@router.put("/{plan_id}", response_model=LessonPlanResponse)
async def update_lesson_plan(
    plan_id: UUID,
    data: LessonPlanUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.PROFESSOR, UserRole.ADMIN, UserRole.SUPERADMIN)),
):
    result = await db.execute(select(LessonPlan).where(LessonPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plano de aula não encontrado")
        
    if current_user.role == UserRole.PROFESSOR and plan.professor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Acesso negado: Plano de aula de outro professor")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(plan, key, value)
    await db.commit()
    await db.refresh(plan)
    return plan


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lesson_plan(
    plan_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.PROFESSOR, UserRole.ADMIN, UserRole.SUPERADMIN)),
):
    result = await db.execute(select(LessonPlan).where(LessonPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plano de aula não encontrado")
        
    if current_user.role == UserRole.PROFESSOR and plan.professor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Acesso negado: Plano de aula de outro professor")
    
    # Delete related attendance and grades first
    await db.execute(delete(Attendance).where(Attendance.lesson_plan_id == plan_id))
    await db.execute(delete(Grade).where(Grade.lesson_plan_id == plan_id))
    await db.delete(plan)
    await db.commit()


@router.get("/", response_model=list[LessonPlanResponse])
async def list_lesson_plans(
    class_group_subject_id: Optional[UUID] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(LessonPlan)
    if class_group_subject_id:
        query = query.where(LessonPlan.class_group_subject_id == class_group_subject_id)
    
    if start_date:
        query = query.where(LessonPlan.date >= start_date)
    if end_date:
        query = query.where(LessonPlan.date <= end_date)
        
    if current_user.role == UserRole.PROFESSOR:
        query = query.where(LessonPlan.professor_id == current_user.id)
        
    query = query.order_by(LessonPlan.date.desc())
    
    
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{plan_id}/details")
async def get_lesson_plan_details(
    plan_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get Attendance and Grades for a Lesson Plan in matrix format"""
    # 1. Fetch Students (via Enrollment from Attendance/Grades or Plan)
    plan_result = await db.execute(select(LessonPlan).where(LessonPlan.id == plan_id))
    plan = plan_result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plano de aula não encontrado")
        
    if current_user.role == UserRole.PROFESSOR and plan.professor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Acesso negado: Plano de aula de outro professor")

    from sqlalchemy.orm import joinedload
    
    # Let's get the specific ClassGroup from the ClassGroupSubject linked to the LessonPlan
    cg_sub_res = await db.execute(select(ClassGroupSubject).where(ClassGroupSubject.id == plan.class_group_subject_id))
    cg_subject = cg_sub_res.scalar_one_or_none()
    
    students_map = {}
    
    if cg_subject:
        # Fetch all active students currently enrolled in this class group
        enrolled_res = await db.execute(
            select(ClassGroupStudent)
            .options(joinedload(ClassGroupStudent.enrollment).joinedload(Enrollment.student))
            .where(
                ClassGroupStudent.class_group_id == cg_subject.class_group_id,
            )
        )
        enrolled_students = enrolled_res.scalars().all()
        
        for e in enrolled_students:
            # Check if enrollment is active, we mostly care about active students
            if e.enrollment and e.enrollment.status == EnrollmentStatus.ACTIVE and e.enrollment.student:
                student_id = e.enrollment.student.id
                students_map[student_id] = {
                    "id": student_id,
                    "name": e.enrollment.student.name,
                    "enrollment_id": e.enrollment.id
                }
    
    # Fetch attendances
    att_result = await db.execute(
        select(Attendance).options(joinedload(Attendance.enrollment).joinedload(Enrollment.student)).where(Attendance.lesson_plan_id == plan_id)
    )
    attendances_db = att_result.scalars().all()
    
    # Fetch grades
    grades_result = await db.execute(
        select(Grade).options(joinedload(Grade.enrollment).joinedload(Enrollment.student)).where(Grade.lesson_plan_id == plan_id)
    )
    grades_db = grades_result.scalars().all()

    # Still add students from attendance/grades in case they were removed from the class group but have history in this plan
    for att in attendances_db:
        if att.enrollment and att.enrollment.student:
            student_id = att.enrollment.student.id
            if student_id not in students_map:
                students_map[student_id] = {
                    "id": student_id,
                    "name": att.enrollment.student.name,
                    "enrollment_id": att.enrollment.id
                }

    for g in grades_db:
        if g.enrollment and g.enrollment.student:
            student_id = g.enrollment.student.id
            if student_id not in students_map:
                students_map[student_id] = {
                    "id": student_id,
                    "name": g.enrollment.student.name,
                    "enrollment_id": g.enrollment.id
                }

    formatted_attendances = []
    for att in attendances_db:
         formatted_attendances.append({
             "id": att.id,
             "enrollment_id": att.enrollment_id,
             "class_order_item": att.class_order_item,
             "present": att.present,
             "observation": att.observation
         })
         
    formatted_grades = []
    for g in grades_db:
         formatted_grades.append({
             "id": g.id,
             "enrollment_id": g.enrollment_id,
             "value": g.value,
             "observations": g.observations
         })

    return {
        "students": list(students_map.values()),
        "attendance": formatted_attendances,
        "grades": formatted_grades
    }

