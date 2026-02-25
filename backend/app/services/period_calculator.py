"""
Period Calculator Service - Business logic for academic period calculations
Calculates school days, available classes, and validates lesson plans against period constraints
"""
from datetime import date, datetime, timedelta
from typing import List, Dict, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.academic_period import AcademicPeriod, NonSchoolDay, NonSchoolDayReason
from app.schemas.academic_period import PeriodStatistics


class PeriodCalculator:
    """Service class for academic period calculations"""

    @staticmethod
    async def calculate_school_days(period: AcademicPeriod, db: AsyncSession) -> int:
        """
        Calculate the number of school days in the period.
        Excludes weekends and non-school days.
        
        Args:
            period: AcademicPeriod instance
            db: Database session
            
        Returns:
            Number of school days
        """
        if not period.start_date or not period.end_date:
            return 0
        
        # Get all non-school days for this period
        result = await db.execute(select(NonSchoolDay).where(
            NonSchoolDay.academic_period_id == period.id
        ))
        non_school_days = result.scalars().all()
        
        # Create a set of dates to exclude
        excluded_dates = {nsd.date for nsd in non_school_days}
        
        # Count school days
        school_days = 0
        current_date = period.start_date
        
        while current_date <= period.end_date:
            # Check if it's a weekend (Saturday=5, Sunday=6)
            is_weekend = current_date.weekday() >= 5
            is_excluded = current_date in excluded_dates
            
            if not is_weekend and not is_excluded:
                school_days += 1
            
            current_date += timedelta(days=1)
        
        return school_days

    @staticmethod
    def calculate_total_days(period: AcademicPeriod) -> int:
        """Calculate total days in the period (including weekends)"""
        if not period.start_date or not period.end_date:
            return 0
        return (period.end_date - period.start_date).days + 1

    @staticmethod
    async def calculate_available_classes(period: AcademicPeriod, db: AsyncSession) -> int:
        """
        Calculate total number of classes available in the period.
        Formula: school_days × classes_per_day × number_of_schedules
        
        Args:
            period: AcademicPeriod instance
            db: Database session
            
        Returns:
            Total number of available classes
        """
        school_days = await PeriodCalculator.calculate_school_days(period, db)
        
        # If no schedules configured, assume 1 per class
        schedules_count = 1
        
        return school_days * period.classes_per_day * schedules_count

    @staticmethod
    async def get_period_statistics(period: AcademicPeriod, db: AsyncSession) -> PeriodStatistics:
        """
        Get comprehensive statistics for the period
        
        Args:
            period: AcademicPeriod instance
            db: Database session
            
        Returns:
            PeriodStatistics schema with all calculated data
        """
        total_days = PeriodCalculator.calculate_total_days(period)
        school_days = await PeriodCalculator.calculate_school_days(period, db)
        total_classes = await PeriodCalculator.calculate_available_classes(period, db)
        
        result_nsd = await db.execute(select(func.count()).select_from(NonSchoolDay).where(
            NonSchoolDay.academic_period_id == period.id
        ))
        non_school_days_count = result_nsd.scalar()
        
        schedules_count = 0
        
        # Check breaks
        # Since relationships are lazy='selectin', they should be populated
        breaks_count = len(period.period_breaks) if period.period_breaks else 0
        
        return PeriodStatistics(
            period_id=period.id,
            period_name=period.name,
            total_days=total_days,
            school_days=school_days,
            non_school_days_count=non_school_days_count,
            total_classes_available=total_classes,
            classes_per_day=period.classes_per_day,
            schedules_count=schedules_count,
            breaks_count=breaks_count,
            start_date=period.start_date,
            end_date=period.end_date
        )

    @staticmethod
    async def is_school_day(check_date: date, period: AcademicPeriod, db: AsyncSession) -> bool:
        """
        Check if a specific date is a school day
        
        Args:
            check_date: Date to check
            period: AcademicPeriod instance
            db: Database session
            
        Returns:
            True if it's a school day, False otherwise
        """
        # Check if date is within period
        if check_date < period.start_date or check_date > period.end_date:
            return False
        
        # Check if it's a weekend
        if check_date.weekday() >= 5:
            return False
        
        # Check if it's a non-school day
        result = await db.execute(select(NonSchoolDay).where(
            NonSchoolDay.academic_period_id == period.id,
            NonSchoolDay.date == check_date
        ))
        non_school_day = result.scalar_one_or_none()
        
        return non_school_day is None

    @staticmethod
    async def validate_lesson_plan_date(
        lesson_date: date,
        period: AcademicPeriod,
        db: AsyncSession
    ) -> Tuple[bool, str]:
        """
        Validate if a lesson plan date is valid for the period
        
        Args:
            lesson_date: Date of the lesson plan
            period: AcademicPeriod instance
            db: Database session
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if date is within period
        if lesson_date < period.start_date:
            return False, f"Data {lesson_date} é anterior ao início do período ({period.start_date})"
        
        if lesson_date > period.end_date:
            return False, f"Data {lesson_date} é posterior ao fim do período ({period.end_date})"
        
        # Check if it's a school day
        is_valid_day = await PeriodCalculator.is_school_day(lesson_date, period, db)
        if not is_valid_day:
            return False, f"Data {lesson_date} não é um dia letivo (fim de semana, feriado ou evento)"
        
        return True, ""

    @staticmethod
    def auto_generate_breaks(
        period: AcademicPeriod
    ) -> List[Dict]:
        """
        Auto-generate period breaks based on break_type
        
        Args:
            period: AcademicPeriod instance
            
        Returns:
            List of dictionaries with break data (order, name, start_date, end_date)
        """
        breaks = []
        if not period.start_date or not period.end_date:
            return breaks
            
        total_days = (period.end_date - period.start_date).days + 1
        
        # Determine number of breaks based on type
        break_counts = {
            "mensal": 12,
            "bimestral": 6,
            "trimestral": 4,
            "quadrimestral": 3,
            "semestral": 2,
            "anual": 1
        }
        
        break_names = {
            "mensal": "Mês",
            "bimestral": "Bimestre",
            "trimestral": "Trimestre",
            "quadrimestral": "Quadrimestre",
            "semestral": "Semestre",
            "anual": "Ano Letivo"
        }
        
        # Use enum value string correctly checking for object type
        try:
            break_type_str = period.break_type.value
        except AttributeError:
            break_type_str = period.break_type
            
        num_breaks = break_counts.get(break_type_str, 1)
        break_name = break_names.get(break_type_str, "Período")
        
        # Calculate days per break
        days_per_break = total_days // num_breaks
        
        current_start = period.start_date
        
        for i in range(num_breaks):
            if i == num_breaks - 1:
                # Last break goes until the end
                current_end = period.end_date
            else:
                current_end = current_start + timedelta(days=days_per_break - 1)
            
            breaks.append({
                "order": i + 1,
                "name": f"{i + 1}º {break_name}",
                "start_date": current_start,
                "end_date": current_end
            })
            
            current_start = current_end + timedelta(days=1)
        
        return breaks
