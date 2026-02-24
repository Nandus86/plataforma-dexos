"""
Courses API - Courses, CurriculumMatrices, Subjects, MatrixSubjects
"""
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User, UserRole
from app.models.course import Course, CurriculumMatrix, Subject, MatrixSubject
from app.schemas.course import (
    CourseCreate, CourseUpdate, CourseResponse,
    SubjectCreate, SubjectUpdate, SubjectResponse,
    MatrixCreate, MatrixUpdate, MatrixResponse,
    MatrixSubjectCreate, MatrixSubjectUpdate, MatrixSubjectResponse,
)
from app.auth.dependencies import get_current_user, require_role, get_current_tenant_id, get_required_tenant_id

router = APIRouter()


# ========== COURSES ==========

@router.get("/", response_model=list[CourseResponse])
async def list_courses(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: Optional[UUID] = Depends(get_current_tenant_id),
):
    """List courses for current tenant"""
    query = select(Course).where(Course.is_active == True)
    if tenant_id:
        query = query.where(Course.tenant_id == tenant_id)
    result = await db.execute(query.order_by(Course.name))
    return result.scalars().all()


@router.post("/", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
async def create_course(
    data: CourseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN)),
    tenant_id: UUID = Depends(get_required_tenant_id),
):
    """Create a course"""
    course = Course(**data.model_dump(), tenant_id=tenant_id)
    db.add(course)
    await db.flush()  # We need the course ID for the matrix
    
    # Auto-generate base matrix
    from datetime import datetime
    matrix = CurriculumMatrix(
        course_id=course.id,
        name="Matriz Base",
        year=datetime.now().year,
        is_active=True
    )
    db.add(matrix)
    
    await db.commit()
    await db.refresh(course)
    return course


@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Curso não encontrado")
    return course


@router.put("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: UUID,
    data: CourseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN)),
):
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Curso não encontrado")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(course, key, value)
    await db.commit()
    await db.refresh(course)
    return course


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(
    course_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN)),
):
    """Soft delete a course (deactivate) or prevent if it has dependents"""
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Curso não encontrado")

    from app.models.course import Subject
    from app.models.class_group import ClassGroup
    
    # Check if there are subjects
    res_subjects = await db.execute(select(Subject).where(Subject.course_id == course_id, Subject.is_active == True))
    if res_subjects.first():
        raise HTTPException(status_code=400, detail="Não é possível apagar um curso que possui disciplinas ativas.")
        
    # Check if there are class groups
    res_cg = await db.execute(select(ClassGroup).where(ClassGroup.course_id == course_id, ClassGroup.is_active == True))
    if res_cg.first():
        raise HTTPException(status_code=400, detail="Não é possível apagar um curso que possui turmas ativas.")

    course.is_active = False
    await db.commit()


@router.put("/{course_id}/link-period", response_model=CourseResponse)
async def link_course_to_period(
    course_id: UUID,
    period_data: dict,  # {"academic_period_id": "uuid" or null}
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.COORDENACAO)),
):
    """Link or unlink a course to an academic period"""
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Curso não encontrado")
    
    academic_period_id = period_data.get("academic_period_id")
    
    # If linking to a period, validate it exists
    if academic_period_id:
        from app.models.academic_period import AcademicPeriod
        period_result = await db.execute(
            select(AcademicPeriod).where(
                AcademicPeriod.id == academic_period_id,
                AcademicPeriod.tenant_id == current_user.tenant_id
            )
        )
        period = period_result.scalar_one_or_none()
        if not period:
            raise HTTPException(status_code=404, detail="Período letivo não encontrado")
    
    course.academic_period_id = academic_period_id
    await db.commit()
    await db.refresh(course)
    
    return course


# ========== SUBJECTS ==========

@router.get("/subjects/", response_model=list[SubjectResponse])
async def list_subjects(
    course_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: Optional[UUID] = Depends(get_current_tenant_id),
):
    from sqlalchemy.orm import selectinload
    query = select(Subject).options(selectinload(Subject.course)).where(Subject.is_active == True)
    if tenant_id:
        query = query.where(Subject.tenant_id == tenant_id)
    if course_id:
        query = query.where(Subject.course_id == course_id)
    result = await db.execute(query.order_by(Subject.name))
    subjects = result.scalars().all()
    return [
        SubjectResponse(
            id=s.id, course_id=s.course_id, name=s.name, code=s.code,
            workload_hours=s.workload_hours, description=s.description,
            tenant_id=s.tenant_id, is_active=s.is_active, created_at=s.created_at,
            course_name=s.course.name if s.course else None,
        )
        for s in subjects
    ]


@router.post("/subjects/", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED)
async def create_subject(
    data: SubjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN)),
    tenant_id: UUID = Depends(get_required_tenant_id),
):
    subject = Subject(**data.model_dump(), tenant_id=tenant_id)
    db.add(subject)
    await db.flush()
    
    # Load course name and auto-link matrix subject if applicable
    course_name = None
    if subject.course_id:
        result = await db.execute(select(Course).where(Course.id == subject.course_id))
        course = result.scalar_one_or_none()
        course_name = course.name if course else None
        
        if course:
            # Auto-create matrix_subject
            from datetime import datetime
            stmt_matrix = select(CurriculumMatrix).where(CurriculumMatrix.course_id == course.id).order_by(CurriculumMatrix.year.desc()).limit(1)
            res_mx = await db.execute(stmt_matrix)
            matrix = res_mx.scalar_one_or_none()
            
            if not matrix:
                matrix = CurriculumMatrix(
                    course_id=course.id,
                    name="Matriz Base",
                    year=datetime.now().year,
                    is_active=True
                )
                db.add(matrix)
                await db.flush()
                
            matrix_subject = MatrixSubject(
                matrix_id=matrix.id,
                subject_id=subject.id,
                semester=1
            )
            db.add(matrix_subject)

    await db.commit()
    await db.refresh(subject)
    
    return SubjectResponse(
        id=subject.id, course_id=subject.course_id, name=subject.name, code=subject.code,
        workload_hours=subject.workload_hours, description=subject.description,
        tenant_id=subject.tenant_id, is_active=subject.is_active, created_at=subject.created_at,
        course_name=course_name,
    )


@router.put("/subjects/{subject_id}", response_model=SubjectResponse)
async def update_subject(
    subject_id: UUID,
    data: SubjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN)),
):
    result = await db.execute(select(Subject).where(Subject.id == subject_id))
    subject = result.scalar_one_or_none()
    if not subject:
        raise HTTPException(status_code=404, detail="Disciplina não encontrada")
        
    old_course_id = subject.course_id
        
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(subject, key, value)
        
    # Check if course changed
    if subject.course_id and subject.course_id != old_course_id:
        # Create matrix_subject for new course
        from datetime import datetime
        stmt_matrix = select(CurriculumMatrix).where(CurriculumMatrix.course_id == subject.course_id).order_by(CurriculumMatrix.year.desc()).limit(1)
        res_mx = await db.execute(stmt_matrix)
        matrix = res_mx.scalar_one_or_none()
        
        if not matrix:
            matrix = CurriculumMatrix(
                course_id=subject.course_id,
                name="Matriz Base",
                year=datetime.now().year,
                is_active=True
            )
            db.add(matrix)
            await db.flush()
            
        # Check if already linked
        stmt_exists = select(MatrixSubject).where(MatrixSubject.matrix_id == matrix.id, MatrixSubject.subject_id == subject.id)
        res_exists = await db.execute(stmt_exists)
        ms_exists = res_exists.scalar_one_or_none()
        
        if not ms_exists:
            matrix_subject = MatrixSubject(
                matrix_id=matrix.id,
                subject_id=subject.id,
                semester=1
            )
            db.add(matrix_subject)
            
    await db.commit()
    await db.refresh(subject)
    course_name = None
    if subject.course_id:
        result = await db.execute(select(Course).where(Course.id == subject.course_id))
        course = result.scalar_one_or_none()
        course_name = course.name if course else None
    return SubjectResponse(
        id=subject.id, course_id=subject.course_id, name=subject.name, code=subject.code,
        workload_hours=subject.workload_hours, description=subject.description,
        tenant_id=subject.tenant_id, is_active=subject.is_active, created_at=subject.created_at,
        course_name=course_name,
    )

@router.delete("/subjects/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subject(
    subject_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN)),
):
    """Soft delete a subject if it is not linked to any active class_group"""
    result = await db.execute(select(Subject).where(Subject.id == subject_id))
    subject = result.scalar_one_or_none()
    if not subject:
        raise HTTPException(status_code=404, detail="Disciplina não encontrada")

    from app.models.class_group import ClassGroupSubject
    from app.models.course import MatrixSubject
    
    # Check if subject is in a class group
    stmt_cg = select(ClassGroupSubject).where(ClassGroupSubject.subject_id == subject_id)
    res_cg = await db.execute(stmt_cg)
    if res_cg.first():
        raise HTTPException(status_code=400, detail="Não é possível apagar uma disciplina vinculada a uma turma.")

    # Deactivate the matrix subject link if any
    stmt_ms = select(MatrixSubject).where(MatrixSubject.subject_id == subject_id)
    res_ms = await db.execute(stmt_ms)
    for ms in res_ms.scalars().all():
        ms.is_active = False

    subject.is_active = False
    await db.commit()


# ========== CURRICULUM MATRICES ==========

@router.get("/{course_id}/matrices/", response_model=list[MatrixResponse])
async def list_matrices(
    course_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(CurriculumMatrix).where(CurriculumMatrix.course_id == course_id).order_by(CurriculumMatrix.year.desc())
    )
    return result.scalars().all()


@router.post("/matrices/", response_model=MatrixResponse, status_code=status.HTTP_201_CREATED)
async def create_matrix(
    data: MatrixCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN)),
):
    matrix = CurriculumMatrix(**data.model_dump())
    db.add(matrix)
    await db.commit()
    await db.refresh(matrix)
    return matrix


@router.put("/matrices/{matrix_id}", response_model=MatrixResponse)
async def update_matrix(
    matrix_id: UUID,
    data: MatrixUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN)),
):
    result = await db.execute(select(CurriculumMatrix).where(CurriculumMatrix.id == matrix_id))
    matrix = result.scalar_one_or_none()
    if not matrix:
        raise HTTPException(status_code=404, detail="Matriz curricular não encontrada")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(matrix, key, value)
    await db.commit()
    await db.refresh(matrix)
    return matrix


# ========== MATRIX SUBJECTS ==========

@router.get("/matrices/{matrix_id}/subjects/", response_model=list[MatrixSubjectResponse])
async def list_matrix_subjects(
    matrix_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(MatrixSubject)
        .options(selectinload(MatrixSubject.subject))
        .where(MatrixSubject.matrix_id == matrix_id)
        .order_by(MatrixSubject.semester)
    )
    matrix_subjects = result.scalars().all()
    
    return [
        MatrixSubjectResponse(
            id=ms.id, matrix_id=ms.matrix_id, subject_id=ms.subject_id,
            professor_id=ms.professor_id, semester=ms.semester, is_active=ms.is_active,
            subject_name=ms.subject.name if ms.subject else None,
            subject_code=ms.subject.code if ms.subject else None,
            workload_hours=ms.subject.workload_hours if ms.subject else None,
        )
        for ms in matrix_subjects
    ]


@router.post("/matrix-subjects/", response_model=MatrixSubjectResponse, status_code=status.HTTP_201_CREATED)
async def create_matrix_subject(
    data: MatrixSubjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN)),
):
    ms = MatrixSubject(**data.model_dump())
    db.add(ms)
    await db.commit()
    await db.refresh(ms)
    return ms


@router.put("/matrix-subjects/{ms_id}", response_model=MatrixSubjectResponse)
async def update_matrix_subject(
    ms_id: UUID,
    data: MatrixSubjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN)),
):
    result = await db.execute(select(MatrixSubject).where(MatrixSubject.id == ms_id))
    ms = result.scalar_one_or_none()
    if not ms:
        raise HTTPException(status_code=404, detail="Disciplina na matriz não encontrada")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(ms, key, value)
    await db.commit()
    await db.refresh(ms)
    return ms
