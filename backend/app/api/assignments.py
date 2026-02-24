"""
Assignments API - Tasks and submissions
"""
from uuid import UUID
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.user import User, UserRole
from app.models.academic import Assignment, AssignmentSubmission
from app.schemas.assignment import (
    AssignmentCreate, AssignmentUpdate, AssignmentResponse,
    SubmissionCreate, SubmissionGrade, SubmissionResponse,
)
from app.auth.dependencies import get_current_user, require_role

router = APIRouter()


# ========== ASSIGNMENTS ==========

@router.get("/", response_model=list[AssignmentResponse])
async def list_assignments(
    matrix_subject_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Assignment).where(Assignment.is_active == True)
    if matrix_subject_id:
        query = query.where(Assignment.matrix_subject_id == matrix_subject_id)
    if current_user.role == UserRole.PROFESSOR:
        query = query.where(Assignment.professor_id == current_user.id)
    result = await db.execute(query.order_by(Assignment.created_at.desc()))
    assignments = result.scalars().all()

    # Add submission count
    response_list = []
    for a in assignments:
        count_result = await db.execute(
            select(func.count()).select_from(AssignmentSubmission).where(
                AssignmentSubmission.assignment_id == a.id
            )
        )
        count = count_result.scalar()
        resp = AssignmentResponse.model_validate(a)
        resp.submissions_count = count
        response_list.append(resp)

    return response_list


@router.post("/", response_model=AssignmentResponse, status_code=status.HTTP_201_CREATED)
async def create_assignment(
    data: AssignmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.PROFESSOR)),
):
    assignment = Assignment(
        **data.model_dump(),
        professor_id=current_user.id,
    )
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)
    return AssignmentResponse.model_validate(assignment)


@router.put("/{assignment_id}", response_model=AssignmentResponse)
async def update_assignment(
    assignment_id: UUID,
    data: AssignmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.PROFESSOR)),
):
    result = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(assignment, key, value)
    await db.commit()
    await db.refresh(assignment)
    return AssignmentResponse.model_validate(assignment)


# ========== SUBMISSIONS ==========

@router.get("/{assignment_id}/submissions/", response_model=list[SubmissionResponse])
async def list_submissions(
    assignment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(AssignmentSubmission).where(AssignmentSubmission.assignment_id == assignment_id)
    if current_user.role == UserRole.ESTUDANTE:
        query = query.where(AssignmentSubmission.student_id == current_user.id)
    result = await db.execute(query.order_by(AssignmentSubmission.submitted_at.desc()))
    return result.scalars().all()


@router.post("/submissions/", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
async def create_submission(
    data: SubmissionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ESTUDANTE)),
):
    """Student submits an assignment"""
    # Check if already submitted
    existing = await db.execute(
        select(AssignmentSubmission).where(
            AssignmentSubmission.assignment_id == data.assignment_id,
            AssignmentSubmission.student_id == current_user.id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Você já enviou esta tarefa")

    submission = AssignmentSubmission(
        **data.model_dump(),
        student_id=current_user.id,
    )
    db.add(submission)
    await db.commit()
    await db.refresh(submission)
    return submission


@router.put("/submissions/{submission_id}/grade", response_model=SubmissionResponse)
async def grade_submission(
    submission_id: UUID,
    data: SubmissionGrade,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.PROFESSOR)),
):
    """Professor grades a submission"""
    result = await db.execute(select(AssignmentSubmission).where(AssignmentSubmission.id == submission_id))
    submission = result.scalar_one_or_none()
    if not submission:
        raise HTTPException(status_code=404, detail="Submissão não encontrada")
    submission.score = data.score
    submission.feedback = data.feedback
    submission.graded_at = datetime.utcnow()
    await db.commit()
    await db.refresh(submission)
    return submission
