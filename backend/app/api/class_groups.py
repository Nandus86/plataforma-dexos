"""
Class Groups API - Turmas CRUD + Students + Subjects + Grid management
"""
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.user import User, UserRole
from app.models.course import Course, Subject
from app.models.academic_period import AcademicPeriod
from app.models.class_group import ClassGroup, ClassGroupStudent, ClassGroupSubject, ClassGroupStudentSubject, ClassGroupSubjectProfessor, ShiftType
from app.schemas.class_group import (
    ClassGroupCreate, ClassGroupUpdate, ClassGroupResponse, ClassGroupDetailResponse,
    ClassGroupStudentCreate, ClassGroupStudentResponse,
    ClassGroupSubjectCreate, ClassGroupSubjectResponse,
    StudentSubjectStatusUpdate, StudentSubjectStatusResponse,
    ProfessorAssignmentCreate, ProfessorAssignmentResponse,
)
from app.auth.dependencies import get_current_user, require_role, get_current_tenant_id, get_required_tenant_id

router = APIRouter()


# ========== HELPER: auto-create grid entries ==========

async def _sync_grid_for_group(db: AsyncSession, group_id: UUID):
    """Ensure ClassGroupStudentSubject rows exist for every enrollment×subject combo in the group."""
    # Get all enrollments and subjects in this group
    students_result = await db.execute(
        select(ClassGroupStudent.enrollment_id).where(ClassGroupStudent.class_group_id == group_id)
    )
    enrollment_ids = [r[0] for r in students_result.all()]

    subjects_result = await db.execute(
        select(ClassGroupSubject.subject_id).where(ClassGroupSubject.class_group_id == group_id)
    )
    subject_ids = [r[0] for r in subjects_result.all()]

    if not enrollment_ids or not subject_ids:
        return

    # Get existing combos
    existing_result = await db.execute(
        select(ClassGroupStudentSubject.enrollment_id, ClassGroupStudentSubject.subject_id)
        .where(ClassGroupStudentSubject.class_group_id == group_id)
    )
    existing = set((r[0], r[1]) for r in existing_result.all())

    # Create missing combos
    for eid in enrollment_ids:
        for subj_id in subject_ids:
            if (eid, subj_id) not in existing:
                db.add(ClassGroupStudentSubject(
                    class_group_id=group_id,
                    enrollment_id=eid,
                    subject_id=subj_id,
                    is_active=True,
                ))

    await db.flush()


# ========== CLASS GROUPS (TURMAS) ==========

@router.get("/", response_model=list[ClassGroupDetailResponse])
async def list_class_groups(
    course_id: Optional[UUID] = Query(None),
    year: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: Optional[UUID] = Depends(get_current_tenant_id),
):
    """List class groups with optional filtering"""
    query = select(ClassGroup).options(
        selectinload(ClassGroup.course),
        selectinload(ClassGroup.students),
        selectinload(ClassGroup.subjects),
        selectinload(ClassGroup.academic_period),
        selectinload(ClassGroup.period_break),
    )

    if tenant_id:
        query = query.where(ClassGroup.tenant_id == tenant_id)
    if course_id:
        query = query.where(ClassGroup.course_id == course_id)
    if year:
        query = query.where(ClassGroup.year == year)
    if is_active is not None:
        query = query.where(ClassGroup.is_active == is_active)

    query = query.order_by(ClassGroup.year.desc(), ClassGroup.semester.desc(), ClassGroup.name)
    result = await db.execute(query)
    groups = result.scalars().unique().all()

    return [
        ClassGroupDetailResponse(
            id=g.id,
            tenant_id=g.tenant_id,
            course_id=g.course_id,
            name=g.name,
            year=g.year,
            semester=g.semester,
            shift=g.shift.value if g.shift else "noite",
            max_students=g.max_students,
            is_active=g.is_active,
            created_at=g.created_at,
            updated_at=g.updated_at,
            course_name=g.course.name if g.course else None,
            student_count=len(g.students) if g.students else 0,
            subject_count=len(g.subjects) if g.subjects else 0,
            academic_period_id=g.academic_period_id,
            period_break_id=g.period_break_id,
            academic_period_name=g.academic_period.name if getattr(g, 'academic_period', None) else None,
            period_break_name=g.period_break.name if getattr(g, 'period_break', None) else None,
        )
        for g in groups
    ]


@router.post("/", response_model=ClassGroupResponse, status_code=status.HTTP_201_CREATED)
async def create_class_group(
    data: ClassGroupCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN)),
    tenant_id: UUID = Depends(get_required_tenant_id),
):
    """Create a class group (turma)"""
    result = await db.execute(select(Course).where(Course.id == data.course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Curso não encontrado")

    # Fetch academic period to get year
    ap_result = await db.execute(select(AcademicPeriod).where(AcademicPeriod.id == data.academic_period_id))
    ap = ap_result.scalar_one_or_none()
    if not ap:
        raise HTTPException(status_code=404, detail="Ano letivo não encontrado")

    group = ClassGroup(
        tenant_id=tenant_id,
        course_id=data.course_id,
        name=data.name,
        year=ap.year,
        semester=data.semester,
        shift=ShiftType(data.shift) if data.shift else ShiftType.NOITE,
        max_students=data.max_students,
        academic_period_id=data.academic_period_id,
        period_break_id=data.period_break_id,
    )
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return group


@router.get("/{group_id}", response_model=ClassGroupDetailResponse)
async def get_class_group(
    group_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get class group details"""
    result = await db.execute(
        select(ClassGroup)
        .options(
            selectinload(ClassGroup.course),
            selectinload(ClassGroup.students),
            selectinload(ClassGroup.subjects),
            selectinload(ClassGroup.academic_period),
            selectinload(ClassGroup.period_break),
        )
        .where(ClassGroup.id == group_id)
    )
    g = result.scalar_one_or_none()
    if not g:
        raise HTTPException(status_code=404, detail="Turma não encontrada")

    return ClassGroupDetailResponse(
        id=g.id,
        tenant_id=g.tenant_id,
        course_id=g.course_id,
        name=g.name,
        year=g.year,
        semester=g.semester,
        shift=g.shift.value if g.shift else "noite",
        max_students=g.max_students,
        is_active=g.is_active,
        created_at=g.created_at,
        updated_at=g.updated_at,
        course_name=g.course.name if g.course else None,
        student_count=len(g.students) if g.students else 0,
        subject_count=len(g.subjects) if g.subjects else 0,
        academic_period_id=g.academic_period_id,
        period_break_id=g.period_break_id,
        academic_period_name=g.academic_period.name if getattr(g, 'academic_period', None) else None,
        period_break_name=g.period_break.name if getattr(g, 'period_break', None) else None,
    )

@router.put("/{group_id}", response_model=ClassGroupResponse)
async def update_class_group(
    group_id: UUID,
    data: ClassGroupUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN)),
):
    """Update a class group"""
    result = await db.execute(select(ClassGroup).where(ClassGroup.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Turma não encontrada")

    update_data = data.model_dump(exclude_unset=True)
    if "shift" in update_data and update_data["shift"]:
        update_data["shift"] = ShiftType(update_data["shift"])

    for key, value in update_data.items():
        setattr(group, key, value)

    await db.commit()
    await db.refresh(group)
    return group


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_class_group(
    group_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN)),
):
    """Soft delete a class group if it's empty"""
    result = await db.execute(select(ClassGroup).where(ClassGroup.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Turma não encontrada")

    # Check for enrolled students
    count_students_res = await db.execute(select(func.count(ClassGroupStudent.id)).where(ClassGroupStudent.class_group_id == group_id))
    if count_students_res.scalar() > 0:
        raise HTTPException(status_code=400, detail="Não é possível apagar uma turma que possui estudantes matriculados.")

    # Check for linked subjects
    count_subjects_res = await db.execute(select(func.count(ClassGroupSubject.id)).where(ClassGroupSubject.class_group_id == group_id))
    if count_subjects_res.scalar() > 0:
        raise HTTPException(status_code=400, detail="Não é possível apagar uma turma que possui disciplinas cadastradas.")

    group.is_active = False
    await db.commit()


# ========== CLASS GROUP STUDENTS ==========

@router.get("/{group_id}/students/", response_model=list[ClassGroupStudentResponse])
async def list_class_group_students(
    group_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List enrollments in a class group"""
    from app.models.academic import Enrollment
    from sqlalchemy.orm import joinedload
    
    result = await db.execute(
        select(ClassGroupStudent)
        .options(joinedload(ClassGroupStudent.enrollment).joinedload(Enrollment.student))
        .where(ClassGroupStudent.class_group_id == group_id)
    )
    records = result.scalars().all()

    return [
        ClassGroupStudentResponse(
            id=r.id,
            class_group_id=r.class_group_id,
            enrollment_id=r.enrollment_id,
            enrolled_at=r.enrolled_at,
            student_name=r.enrollment.student.name if r.enrollment and r.enrollment.student else None,
            student_email=r.enrollment.student.email if r.enrollment and r.enrollment.student else None,
            registration_number=r.enrollment.student.registration_number if r.enrollment and r.enrollment.student else None,
        )
        for r in records
    ]


@router.post("/{group_id}/students/", response_model=ClassGroupStudentResponse, status_code=status.HTTP_201_CREATED)
async def add_student_to_class_group(
    group_id: UUID,
    data: ClassGroupStudentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.COORDENACAO)),
):
    """Add an enrollment to a class group and auto-create grid entries"""
    from app.models.academic import Enrollment
    from sqlalchemy.orm import joinedload
    
    result = await db.execute(select(ClassGroup).where(ClassGroup.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Turma não encontrada")

    # Fetch Enrollment and ensure it matches the same Course as the ClassGroup
    enrollment_result = await db.execute(
        select(Enrollment)
        .options(joinedload(Enrollment.student))
        .where(Enrollment.id == data.enrollment_id, Enrollment.course_id == group.course_id)
    )
    enrollment = enrollment_result.scalar_one_or_none()
    
    if not enrollment:
        raise HTTPException(
            status_code=400, 
            detail="Matrícula inválida ou não pertence ao curso desta turma."
        )

    existing = await db.execute(
        select(ClassGroupStudent).where(
            ClassGroupStudent.class_group_id == group_id,
            ClassGroupStudent.enrollment_id == data.enrollment_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Aluno já está na turma")

    if group.max_students:
        count_result = await db.execute(
            select(func.count()).where(ClassGroupStudent.class_group_id == group_id)
        )
        current_count = count_result.scalar()
        if current_count >= group.max_students:
            raise HTTPException(status_code=400, detail="Turma está cheia")

    record = ClassGroupStudent(class_group_id=group_id, enrollment_id=data.enrollment_id)
    db.add(record)
    await db.flush()

    # Auto-create grid entries for this student × all subjects
    await _sync_grid_for_group(db, group_id)
    await db.commit()
    await db.refresh(record)

    return ClassGroupStudentResponse(
        id=record.id,
        class_group_id=record.class_group_id,
        enrollment_id=record.enrollment_id,
        enrolled_at=record.enrolled_at,
        student_name=enrollment.student.name,
        student_email=enrollment.student.email,
        registration_number=enrollment.student.registration_number,
    )


@router.delete("/{group_id}/students/{enrollment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_student_from_class_group(
    group_id: UUID,
    enrollment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.COORDENACAO)),
):
    """Remove an enrollment from a class group (also removes grid entries)"""
    result = await db.execute(
        select(ClassGroupStudent).where(
            ClassGroupStudent.class_group_id == group_id,
            ClassGroupStudent.enrollment_id == enrollment_id,
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Matrícula não encontrada na turma")

    # Remove grid entries for this enrollment
    grid_result = await db.execute(
        select(ClassGroupStudentSubject).where(
            ClassGroupStudentSubject.class_group_id == group_id,
            ClassGroupStudentSubject.enrollment_id == enrollment_id,
        )
    )
    for gr in grid_result.scalars().all():
        await db.delete(gr)

    await db.delete(record)
    await db.commit()


# ========== CLASS GROUP SUBJECTS ==========

@router.get("/{group_id}/subjects/", response_model=list[ClassGroupSubjectResponse])
async def list_class_group_subjects(
    group_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List subjects in a class group"""
    result = await db.execute(
        select(ClassGroupSubject)
        .options(
            selectinload(ClassGroupSubject.subject),
            selectinload(ClassGroupSubject.professors).selectinload(ClassGroupSubjectProfessor.professor),
        )
        .where(ClassGroupSubject.class_group_id == group_id)
    )
    records = result.scalars().all()

    return [
        ClassGroupSubjectResponse(
            id=r.id,
            class_group_id=r.class_group_id,
            subject_id=r.subject_id,
            subject_name=r.subject.name if r.subject else None,
            workload_hours=r.subject.workload_hours if r.subject else 0,
            professors=[
                ProfessorAssignmentResponse(
                    professor_id=p.professor_id,
                    professor_name=p.professor.name if p.professor else "Desconhecido",
                    assigned_hours=p.assigned_hours
                )
                for p in r.professors
            ]
        )
        for r in records
    ]


@router.post("/{group_id}/subjects/", response_model=ClassGroupSubjectResponse, status_code=status.HTTP_201_CREATED)
async def add_subject_to_class_group(
    group_id: UUID,
    data: ClassGroupSubjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.COORDENACAO)),
):
    """Add a subject to a class group and auto-create grid entries"""
    result = await db.execute(select(ClassGroup).where(ClassGroup.id == group_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Turma não encontrada")

    result = await db.execute(select(Subject).where(Subject.id == data.subject_id))
    subject = result.scalar_one_or_none()
    if not subject:
        raise HTTPException(status_code=404, detail="Disciplina não encontrada")

    existing = await db.execute(
        select(ClassGroupSubject).where(
            ClassGroupSubject.class_group_id == group_id,
            ClassGroupSubject.subject_id == data.subject_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Disciplina já adicionada à turma")

    if not data.professors:
        raise HTTPException(status_code=400, detail="É obrigatório informar pelo menos um professor.")

    record = ClassGroupSubject(
        class_group_id=group_id,
        subject_id=data.subject_id,
    )
    db.add(record)
    await db.flush()

    # Add professors
    assigned_professors = []
    if data.professors:
        for p_data in data.professors:
            # Verify professor exists
            prof_res = await db.execute(select(User).where(User.id == p_data.professor_id))
            professor = prof_res.scalar_one_or_none()
            
            link = ClassGroupSubjectProfessor(
                class_group_subject_id=record.id,
                professor_id=p_data.professor_id,
                assigned_hours=p_data.assigned_hours
            )
            db.add(link)
            
            if professor:
                assigned_professors.append(
                    ProfessorAssignmentResponse(
                        professor_id=professor.id,
                        professor_name=professor.name,
                        assigned_hours=p_data.assigned_hours
                    )
                )
    
    # Auto-create grid entries for all students × this subject
    await _sync_grid_for_group(db, group_id)
    await db.commit()
    await db.refresh(record)

    return ClassGroupSubjectResponse(
        id=record.id,
        class_group_id=record.class_group_id,
        subject_id=record.subject_id,
        subject_name=subject.name,
        professors=assigned_professors
    )


@router.delete("/{group_id}/subjects/{cg_subject_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_subject_from_class_group(
    group_id: UUID,
    cg_subject_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.COORDENACAO)),
):
    """Remove a subject from a class group (also removes grid entries)"""
    result = await db.execute(
        select(ClassGroupSubject).where(
            ClassGroupSubject.class_group_id == group_id,
            ClassGroupSubject.id == cg_subject_id,
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Disciplina não encontrada na turma")

    from app.models.content import LessonPlan
    res_lessons = await db.execute(select(LessonPlan).where(LessonPlan.class_group_subject_id == cg_subject_id))
    if res_lessons.first():
        raise HTTPException(status_code=400, detail="Não é possível remover a disciplina pois existem planos de aula cadastrados para ela nesta turma.")

    # Remove grid entries for this subject
    grid_result = await db.execute(
        select(ClassGroupStudentSubject).where(
            ClassGroupStudentSubject.class_group_id == group_id,
            ClassGroupStudentSubject.subject_id == record.subject_id,
        )
    )
    for gr in grid_result.scalars().all():
        await db.delete(gr)

    await db.delete(record)
    await db.commit()


# ========== STUDENT-SUBJECT GRID ==========

@router.get("/{group_id}/grid/", response_model=list[StudentSubjectStatusResponse])
async def get_grid(
    group_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get full student×subject grid for a class group"""
    from app.models.academic import Enrollment
    from sqlalchemy.orm import joinedload
    
    # Ensure grid is synced
    await _sync_grid_for_group(db, group_id)
    await db.commit()

    result = await db.execute(
        select(ClassGroupStudentSubject)
        .options(
            joinedload(ClassGroupStudentSubject.enrollment).joinedload(Enrollment.student),
            selectinload(ClassGroupStudentSubject.subject),
        )
        .where(ClassGroupStudentSubject.class_group_id == group_id)
    )
    records = result.scalars().all()

    return [
        StudentSubjectStatusResponse(
            id=r.id,
            class_group_id=r.class_group_id,
            enrollment_id=r.enrollment_id,
            subject_id=r.subject_id,
            is_active=r.is_active,
            reason=r.reason,
            student_name=r.enrollment.student.name if r.enrollment and r.enrollment.student else None,
            subject_name=r.subject.name if r.subject else None,
        )
        for r in records
    ]


@router.put("/{group_id}/grid/{enrollment_id}/{subject_id}", response_model=StudentSubjectStatusResponse)
async def update_grid_status(
    group_id: UUID,
    enrollment_id: UUID,
    subject_id: UUID,
    data: StudentSubjectStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.COORDENACAO)),
):
    """Update a student's status in a specific subject within a class group"""
    from app.models.academic import Enrollment
    from sqlalchemy.orm import joinedload
    
    result = await db.execute(
        select(ClassGroupStudentSubject)
        .options(
            joinedload(ClassGroupStudentSubject.enrollment).joinedload(Enrollment.student),
            selectinload(ClassGroupStudentSubject.subject),
        )
        .where(
            ClassGroupStudentSubject.class_group_id == group_id,
            ClassGroupStudentSubject.enrollment_id == enrollment_id,
            ClassGroupStudentSubject.subject_id == subject_id,
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Registro não encontrado na grade")

    record.is_active = data.is_active
    record.reason = data.reason if not data.is_active else None
    await db.commit()
    await db.refresh(record)

    return StudentSubjectStatusResponse(
        id=record.id,
        class_group_id=record.class_group_id,
        enrollment_id=record.enrollment_id,
        subject_id=record.subject_id,
        is_active=record.is_active,
        reason=record.reason,
        student_name=record.enrollment.student.name if record.enrollment and record.enrollment.student else None,
        subject_name=record.subject.name if record.subject else None,
    )
