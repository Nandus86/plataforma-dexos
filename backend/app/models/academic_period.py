"""
Academic Period Models - AcademicPeriod, PeriodBreak, NonSchoolDay, ClassSchedule
Parametrização completa do período letivo para controle de planos de aula
"""
import uuid
import enum
from datetime import datetime, time, date

from sqlalchemy import Column, String, Boolean, DateTime, Integer, Enum, ForeignKey, Date, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class BreakType(str, enum.Enum):
    """Tipos de quebra de período letivo"""
    MONTHLY = "mensal"
    BIMONTHLY = "bimestral"
    QUARTERLY = "trimestral"
    FOURMONTHLY = "quadrimestral"
    SEMIANNUAL = "semestral"
    ANNUAL = "anual"


class NonSchoolDayReason(str, enum.Enum):
    """Motivos de dias sem aula"""
    SATURDAY = "sabado"
    SUNDAY = "domingo"
    HOLIDAY = "feriado"
    EVENT = "evento"
    RECESS = "recesso"
    OTHER = "outro"


class AcademicPeriod(Base):
    """Período letivo com todas as parametrizações"""
    __tablename__ = "academic_periods"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)  # Ex: "Período 2026.1"
    year = Column(Integer, nullable=False)
    break_type = Column(Enum(BreakType, values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    classes_per_day = Column(Integer, default=1)  # Quantidade de aulas por dia
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant")
    period_breaks = relationship("PeriodBreak", back_populates="academic_period", lazy="selectin", cascade="all, delete-orphan")
    non_school_days = relationship("NonSchoolDay", back_populates="academic_period", lazy="selectin", cascade="all, delete-orphan")
    extra_school_days = relationship("ExtraSchoolDay", back_populates="academic_period", lazy="selectin", cascade="all, delete-orphan")
    courses = relationship("Course", back_populates="academic_period")

    def __repr__(self):
        return f"<AcademicPeriod {self.name} ({self.year})>"


class PeriodBreak(Base):
    """Quebras do período (bimestre, trimestre, etc)"""
    __tablename__ = "period_breaks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    academic_period_id = Column(UUID(as_uuid=True), ForeignKey("academic_periods.id", ondelete="CASCADE"), nullable=False, index=True)
    order = Column(Integer, nullable=False)  # 1º bimestre, 2º bimestre, etc
    name = Column(String(100), nullable=False)  # Ex: "1º Bimestre"
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    # Relationships
    academic_period = relationship("AcademicPeriod", back_populates="period_breaks")

    def __repr__(self):
        return f"<PeriodBreak {self.name} ({self.start_date} - {self.end_date})>"


class NonSchoolDay(Base):
    """Dias que não terão aula (feriados, eventos, finais de semana, etc)"""
    __tablename__ = "non_school_days"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    academic_period_id = Column(UUID(as_uuid=True), ForeignKey("academic_periods.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False)
    reason = Column(Enum(NonSchoolDayReason, values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    description = Column(String(255), nullable=True)  # Descrição do feriado/evento

    # Relationships
    academic_period = relationship("AcademicPeriod", back_populates="non_school_days")

    def __repr__(self):
        return f"<NonSchoolDay {self.date} - {self.reason.value}>"


class ExtraSchoolDay(Base):
    """Dias letivos extras (ex: sábados letivos/reposição)"""
    __tablename__ = "extra_school_days"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    academic_period_id = Column(UUID(as_uuid=True), ForeignKey("academic_periods.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False)
    description = Column(String(255), nullable=True)

    # Relationships
    academic_period = relationship("AcademicPeriod", back_populates="extra_school_days")

    def __repr__(self):
        return f"<ExtraSchoolDay {self.date}>"
