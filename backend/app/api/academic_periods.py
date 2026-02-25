"""
Academic Periods API - CRUD operations and period management
"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.database import get_db
from app.auth.dependencies import get_current_user, get_current_tenant_id, get_required_tenant_id
from typing import Optional
from app.models.user import User, UserRole
from app.models.academic_period import AcademicPeriod, PeriodBreak, NonSchoolDay, NonSchoolDayReason
from app.models.course import Course
from app.schemas.academic_period import (
    AcademicPeriodCreate,
    AcademicPeriodUpdate,
    AcademicPeriodResponse,
    PeriodBreakCreate,
    PeriodBreakResponse,
    NonSchoolDayCreate,
    NonSchoolDayResponse,
    PeriodStatistics
)
from app.services.period_calculator import PeriodCalculator

router = APIRouter(tags=["Academic Periods"])


def require_admin(current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_required_tenant_id)):
    """Require admin or coordenacao role"""
    if current_user.role not in [UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.COORDENACAO]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado. Apenas administradores e coordenação podem gerenciar períodos letivos."
        )
    return current_user


@router.get("", response_model=List[AcademicPeriodResponse])
async def list_academic_periods(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_required_tenant_id),
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False
):
    """List all academic periods for the tenant"""
    query = select(AcademicPeriod).where(
        AcademicPeriod.tenant_id == tenant_id
    )
    
    if active_only:
        query = query.where(AcademicPeriod.is_active == True)
    
    query = query.order_by(AcademicPeriod.year.desc(), AcademicPeriod.start_date.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    periods = result.scalars().all()
    return periods


@router.post("", response_model=AcademicPeriodResponse, status_code=status.HTTP_201_CREATED)
async def create_academic_period(
    period_data: AcademicPeriodCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
    tenant_id: UUID = Depends(get_required_tenant_id)
):
    """Create a new academic period with auto-generated breaks"""
    print(f"DEBUG: Creating period payload: {period_data.model_dump()}")
    # Validate dates
    if period_data.start_date >= period_data.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Data de início deve ser anterior à data de fim"
        )
    
    # Create the period
    period = AcademicPeriod(
        tenant_id=tenant_id,
        **period_data.model_dump()
    )
    
    db.add(period)
    await db.flush()  # Get the ID without committing
    
    # Auto-generate breaks
    # Note: auto_generate_breaks is synchronous logic, no await needed
    breaks_data = PeriodCalculator.auto_generate_breaks(period)
    for break_data in breaks_data:
        period_break = PeriodBreak(
            academic_period_id=period.id,
            **break_data
        )
        db.add(period_break)
    
    await db.commit()
    await db.refresh(period)
    
    return period


@router.get("/{period_id}", response_model=AcademicPeriodResponse)
async def get_academic_period(
    period_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_required_tenant_id)
):
    """Get a specific academic period by ID"""
    result = await db.execute(select(AcademicPeriod).where(
        AcademicPeriod.id == period_id,
        AcademicPeriod.tenant_id == tenant_id
    ))
    period = result.scalar_one_or_none()
    
    if not period:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Período letivo não encontrado"
        )
    
    return period


@router.put("/{period_id}", response_model=AcademicPeriodResponse)
async def update_academic_period(
    period_id: UUID,
    period_data: AcademicPeriodUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
    tenant_id: UUID = Depends(get_required_tenant_id)
):
    """Update an academic period"""
    result = await db.execute(select(AcademicPeriod).where(
        AcademicPeriod.id == period_id,
        AcademicPeriod.tenant_id == tenant_id
    ))
    period = result.scalar_one_or_none()
    
    if not period:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Período letivo não encontrado"
        )
    
    # Update fields
    update_data = period_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(period, field, value)
    
    # Validate dates if both are present
    if period.start_date >= period.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Data de início deve ser anterior à data de fim"
        )
    
    await db.commit()
    await db.refresh(period)
    
    return period


@router.delete("/{period_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_academic_period(
    period_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
    tenant_id: UUID = Depends(get_required_tenant_id)
):
    """Delete an academic period"""
    result = await db.execute(select(AcademicPeriod).where(
        AcademicPeriod.id == period_id,
        AcademicPeriod.tenant_id == tenant_id
    ))
    period = result.scalar_one_or_none()
    
    if not period:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Período letivo não encontrado"
        )
    
    # Check if any courses are linked to this period
    # Manual check to avoid async lazy loading issues
    result_courses = await db.execute(select(Course).where(Course.academic_period_id == period_id).limit(1))
    linked_course = result_courses.scalar_one_or_none()
    
    if linked_course:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é possível excluir o período pois existem cursos vinculados a ele."
        )
    
    await db.delete(period)
    await db.commit()


@router.get("/{period_id}/statistics", response_model=PeriodStatistics)
async def get_period_statistics(
    period_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_required_tenant_id)
):
    """Get calculated statistics for the period"""
    result = await db.execute(select(AcademicPeriod).where(
        AcademicPeriod.id == period_id,
        AcademicPeriod.tenant_id == tenant_id
    ))
    period = result.scalar_one_or_none()
    
    if not period:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Período letivo não encontrado"
        )
    
    return await PeriodCalculator.get_period_statistics(period, db)


# ============= Period Breaks =============

@router.post("/{period_id}/breaks", response_model=PeriodBreakResponse, status_code=status.HTTP_201_CREATED)
async def add_period_break(
    period_id: UUID,
    break_data: PeriodBreakCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
    tenant_id: UUID = Depends(get_required_tenant_id)
):
    """Add a period break"""
    result = await db.execute(select(AcademicPeriod).where(
        AcademicPeriod.id == period_id,
        AcademicPeriod.tenant_id == tenant_id
    ))
    period = result.scalar_one_or_none()
    
    if not period:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Período letivo não encontrado"
        )
    
    # Validate dates within period
    if break_data.start_date < period.start_date or break_data.end_date > period.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="As datas da quebra devem estar dentro do período letivo"
        )
    
    period_break = PeriodBreak(
        academic_period_id=period_id,
        **break_data.model_dump()
    )
    
    db.add(period_break)
    await db.commit()
    await db.refresh(period_break)
    
    return period_break


@router.delete("/breaks/{break_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_period_break(
    break_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
    tenant_id: UUID = Depends(get_required_tenant_id)
):
    """Delete a period break"""
    result = await db.execute(select(PeriodBreak).join(AcademicPeriod).where(
        PeriodBreak.id == break_id,
        AcademicPeriod.tenant_id == tenant_id
    ))
    period_break = result.scalar_one_or_none()
    
    if not period_break:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quebra de período não encontrada"
        )
    
    await db.delete(period_break)
    await db.commit()


# ============= Non-School Days =============

@router.post("/{period_id}/non-school-days", response_model=NonSchoolDayResponse, status_code=status.HTTP_201_CREATED)
async def add_non_school_day(
    period_id: UUID,
    day_data: NonSchoolDayCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
    tenant_id: UUID = Depends(get_required_tenant_id)
):
    """Add a non-school day"""
    result = await db.execute(select(AcademicPeriod).where(
        AcademicPeriod.id == period_id,
        AcademicPeriod.tenant_id == tenant_id
    ))
    period = result.scalar_one_or_none()
    
    if not period:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Período letivo não encontrado"
        )
    
    # Validate date within period
    if day_data.date < period.start_date or day_data.date > period.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A data deve estar dentro do período letivo"
        )
    
    non_school_day = NonSchoolDay(
        academic_period_id=period_id,
        **day_data.model_dump()
    )
    
    db.add(non_school_day)
    await db.commit()
    await db.refresh(non_school_day)
    
    return non_school_day


@router.delete("/non-school-days/{day_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_non_school_day(
    day_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
    tenant_id: UUID = Depends(get_required_tenant_id)
):
    """Delete a non-school day"""
    result = await db.execute(select(NonSchoolDay).join(AcademicPeriod).where(
        NonSchoolDay.id == day_id,
        AcademicPeriod.tenant_id == tenant_id
    ))
    non_school_day = result.scalar_one_or_none()
    
    if not non_school_day:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dia sem aula não encontrado"
        )
    
    await db.delete(non_school_day)
    await db.commit()



# ============= Holidays Import =============

@router.post("/{period_id}/import-holidays", status_code=status.HTTP_201_CREATED)
async def import_holidays(
    period_id: UUID,
    country_code: str = "BR",
    subdiv: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
    tenant_id: UUID = Depends(get_required_tenant_id)
):
    """Import national holidays for the period year"""
    try:
        import holidays
    except ImportError:
        raise HTTPException(status_code=500, detail="Holidays library not installed")

    result = await db.execute(select(AcademicPeriod).where(
        AcademicPeriod.id == period_id,
        AcademicPeriod.tenant_id == tenant_id
    ))
    period = result.scalar_one_or_none()
    
    if not period:
        raise HTTPException(status_code=404, detail="Período letivo não encontrado")

    # Get holidays for the period year
    try:
        if subdiv:
            period_holidays = holidays.country_holidays(country_code, subdiv=subdiv, years=period.year)
        else:
            period_holidays = holidays.country_holidays(country_code, years=period.year)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao buscar feriados: {str(e)}")

    added_count = 0
    
    for date, name in period_holidays.items():
        # Check if date is within period
        if date < period.start_date or date > period.end_date:
            continue
            
        # Check if already exists
        exists_result = await db.execute(select(NonSchoolDay).where(
            NonSchoolDay.academic_period_id == period.id,
            NonSchoolDay.date == date
        ))
        if exists_result.scalar_one_or_none():
            continue
            
        non_school_day = NonSchoolDay(
            academic_period_id=period.id,
            date=date,
            reason=NonSchoolDayReason.HOLIDAY,
            description=name
        )
        db.add(non_school_day)
        added_count += 1
    
    await db.commit()
    return {"message": f"{added_count} feriados importados com sucesso", "count": added_count}


# ============= Extra School Days =============

from app.models.academic_period import ExtraSchoolDay
from app.schemas.academic_period import ExtraSchoolDayCreate, ExtraSchoolDayResponse

@router.post("/{period_id}/extra-school-days", response_model=ExtraSchoolDayResponse, status_code=status.HTTP_201_CREATED)
async def add_extra_school_day(
    period_id: UUID,
    day_data: ExtraSchoolDayCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
    tenant_id: UUID = Depends(get_required_tenant_id)
):
    """Add an extra school day"""
    result = await db.execute(select(AcademicPeriod).where(
        AcademicPeriod.id == period_id,
        AcademicPeriod.tenant_id == tenant_id
    ))
    period = result.scalar_one_or_none()
    
    if not period:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Período letivo não encontrado"
        )
    
    extra_day = ExtraSchoolDay(
        academic_period_id=period_id,
        **day_data.model_dump()
    )
    
    db.add(extra_day)
    await db.commit()
    await db.refresh(extra_day)
    
    return extra_day

@router.delete("/extra-school-days/{day_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_extra_school_day(
    day_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
    tenant_id: UUID = Depends(get_required_tenant_id)
):
    """Delete an extra school day"""
    result = await db.execute(select(ExtraSchoolDay).join(AcademicPeriod).where(
        ExtraSchoolDay.id == day_id,
        AcademicPeriod.tenant_id == tenant_id
    ))
    extra_day = result.scalar_one_or_none()
    
    if not extra_day:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dia letivo extra não encontrado"
        )
    
    await db.delete(extra_day)
    await db.commit()
