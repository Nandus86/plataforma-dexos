
-- Migration 004: Lesson Plans, Attendance and Grades integration

-- 1. Update Lesson Plans table
-- Create ActivityType enum if not exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'activitytype') THEN
        CREATE TYPE activitytype AS ENUM ('none', 'exam', 'work', 'other');
    END IF;
END $$;
-- STATEMENT_END

-- Add columns to lesson_plans
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='lesson_plans' AND column_name='activity_type') THEN
        ALTER TABLE lesson_plans ADD COLUMN activity_type activitytype DEFAULT 'none';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='lesson_plans' AND column_name='description') THEN
        ALTER TABLE lesson_plans ADD COLUMN description TEXT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='lesson_plans' AND column_name='other_activity_reason') THEN
        ALTER TABLE lesson_plans ADD COLUMN other_activity_reason TEXT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='lesson_plans' AND column_name='max_score') THEN
        ALTER TABLE lesson_plans ADD COLUMN max_score DOUBLE PRECISION DEFAULT 10.0;
    END IF;
END $$;
-- STATEMENT_END

-- 2. Update Attendances table
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='attendances' AND column_name='lesson_plan_id') THEN
        ALTER TABLE attendances ADD COLUMN lesson_plan_id UUID REFERENCES lesson_plans(id);
    END IF;
END $$;
-- STATEMENT_END

CREATE INDEX IF NOT EXISTS ix_attendances_lesson_plan_id ON attendances(lesson_plan_id);
-- STATEMENT_END

-- 3. Update Grades table
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='grades' AND column_name='lesson_plan_id') THEN
        ALTER TABLE grades ADD COLUMN lesson_plan_id UUID REFERENCES lesson_plans(id);
    END IF;
END $$;
-- STATEMENT_END

CREATE INDEX IF NOT EXISTS ix_grades_lesson_plan_id ON grades(lesson_plan_id);
-- STATEMENT_END
