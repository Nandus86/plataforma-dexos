-- Migration: Add Academic Period System Tables
-- Description: Creates tables for academic periods, breaks, non-school days, and class schedules
-- Date: 2026-02-17

-- Create ENUM types for PostgreSQL
CREATE TYPE break_type AS ENUM ('mensal', 'bimestral', 'trimestral', 'quadrimestral', 'semestral', 'anual');
CREATE TYPE non_school_day_reason AS ENUM ('sabado', 'domingo', 'feriado', 'evento', 'outro');

-- Create academic_periods table
CREATE TABLE IF NOT EXISTS academic_periods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    year INTEGER NOT NULL,
    break_type break_type NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    classes_per_day INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_academic_periods_tenant ON academic_periods(tenant_id);
CREATE INDEX idx_academic_periods_active ON academic_periods(is_active);

-- Create period_breaks table
CREATE TABLE IF NOT EXISTS period_breaks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    academic_period_id UUID NOT NULL REFERENCES academic_periods(id) ON DELETE CASCADE,
    "order" INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_period_breaks_period ON period_breaks(academic_period_id);

-- Create non_school_days table
CREATE TABLE IF NOT EXISTS non_school_days (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    academic_period_id UUID NOT NULL REFERENCES academic_periods(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    reason non_school_day_reason NOT NULL,
    description VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_non_school_days_period ON non_school_days(academic_period_id);
CREATE INDEX idx_non_school_days_date ON non_school_days(date);

-- Create class_schedules table
CREATE TABLE IF NOT EXISTS class_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    academic_period_id UUID NOT NULL REFERENCES academic_periods(id) ON DELETE CASCADE,
    "order" INTEGER NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_class_schedules_period ON class_schedules(academic_period_id);

-- Add academic_period_id to courses table
ALTER TABLE courses ADD COLUMN IF NOT EXISTS academic_period_id UUID REFERENCES academic_periods(id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_courses_academic_period ON courses(academic_period_id);

-- Add class_group_subject_id and class_order to lesson_plans table
ALTER TABLE lesson_plans ADD COLUMN IF NOT EXISTS class_group_subject_id UUID REFERENCES class_group_subjects(id) ON DELETE SET NULL;
ALTER TABLE lesson_plans ADD COLUMN IF NOT EXISTS class_order INTEGER;
CREATE INDEX IF NOT EXISTS idx_lesson_plans_class_group_subject ON lesson_plans(class_group_subject_id);

-- Trigger to update updated_at on academic_periods
CREATE OR REPLACE FUNCTION update_academic_periods_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_academic_periods_updated_at
    BEFORE UPDATE ON academic_periods
    FOR EACH ROW
    EXECUTE FUNCTION update_academic_periods_updated_at();
