-- 1. Add academic_period_id to class_groups
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='class_groups' AND column_name='academic_period_id') THEN
        ALTER TABLE class_groups ADD COLUMN academic_period_id UUID REFERENCES academic_periods(id);
    END IF;
END $$;
-- STATEMENT_END

DROP INDEX IF EXISTS ix_class_groups_academic_period_id;
-- STATEMENT_END

CREATE INDEX ix_class_groups_academic_period_id ON class_groups(academic_period_id);
-- STATEMENT_END

-- 2. Add period_break_id to class_group_subjects
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='class_group_subjects' AND column_name='period_break_id') THEN
        ALTER TABLE class_group_subjects ADD COLUMN period_break_id UUID REFERENCES period_breaks(id);
    END IF;
END $$;
-- STATEMENT_END

DROP INDEX IF EXISTS ix_class_group_subjects_period_break_id;
-- STATEMENT_END

CREATE INDEX ix_class_group_subjects_period_break_id ON class_group_subjects(period_break_id);
-- STATEMENT_END

-- 3. Add 'recesso' to NonSchoolDayReason enum
ALTER TYPE nonschooldayreason ADD VALUE IF NOT EXISTS 'recesso';
-- STATEMENT_END

-- 4. Create extra_school_days table (if not handled by create_all)
CREATE TABLE IF NOT EXISTS extra_school_days (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    academic_period_id UUID NOT NULL REFERENCES academic_periods(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    description VARCHAR(255),
    CONSTRAINT fk_academic_period FOREIGN KEY (academic_period_id) REFERENCES academic_periods(id) ON DELETE CASCADE
);
-- STATEMENT_END

DROP INDEX IF EXISTS ix_extra_school_days_academic_period_id;
-- STATEMENT_END

CREATE INDEX ix_extra_school_days_academic_period_id ON extra_school_days(academic_period_id);
-- STATEMENT_END
