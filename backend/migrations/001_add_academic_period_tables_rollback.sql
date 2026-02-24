-- Rollback Migration: Remove Academic Period System Tables
-- Description: Reverts all changes made by 001_add_academic_period_tables.sql
-- Date: 2026-02-17

-- Remove columns from lesson_plans
ALTER TABLE lesson_plans DROP COLUMN IF EXISTS class_order;
ALTER TABLE lesson_plans DROP COLUMN IF EXISTS class_group_subject_id;

-- Remove column from courses
ALTER TABLE courses DROP COLUMN IF EXISTS academic_period_id;

-- Drop tables (in reverse order due to foreign keys)
DROP TABLE IF EXISTS class_schedules;
DROP TABLE IF EXISTS non_school_days;
DROP TABLE IF EXISTS period_breaks;
DROP TABLE IF EXISTS academic_periods;

-- Drop trigger and function
DROP TRIGGER IF EXISTS trigger_academic_periods_updated_at ON academic_periods;
DROP FUNCTION IF EXISTS update_academic_periods_updated_at();

-- Drop ENUM types
DROP TYPE IF EXISTS non_school_day_reason;
DROP TYPE IF EXISTS break_type;
