
-- Add period_break_id to class_groups to allow defining duration (e.g. Semester 1 vs Whole Year)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='class_groups' AND column_name='period_break_id') THEN
        ALTER TABLE class_groups ADD COLUMN period_break_id UUID REFERENCES period_breaks(id);
    END IF;
END $$;
-- STATEMENT_END

DROP INDEX IF EXISTS ix_class_groups_period_break_id;
-- STATEMENT_END

CREATE INDEX ix_class_groups_period_break_id ON class_groups(period_break_id);
-- STATEMENT_END
