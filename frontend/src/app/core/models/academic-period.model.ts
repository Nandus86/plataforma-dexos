/**
 * Academic Period Models and Interfaces
 */

export enum BreakType {
    MONTHLY = 'mensal',
    BIMONTHLY = 'bimestral',
    QUARTERLY = 'trimestral',
    FOURMONTHLY = 'quadrimestral',
    SEMIANNUAL = 'semestral',
    ANNUAL = 'anual'
}

export enum NonSchoolDayReason {
    SATURDAY = 'sabado',
    SUNDAY = 'domingo',
    HOLIDAY = 'feriado',
    EVENT = 'evento',
    RECESS = 'recesso',
    OTHER = 'outro'
}

export interface PeriodBreak {
    id: string;
    academic_period_id: string;
    order: number;
    name: string;
    start_date: string;
    end_date: string;
}

export interface NonSchoolDay {
    id: string;
    academic_period_id: string;
    date: string;
    reason: NonSchoolDayReason;
    description?: string;
}

export interface ExtraSchoolDay {
    id: string;
    academic_period_id: string;
    date: string;
    description?: string;
}

export interface ClassSchedule {
    id: string;
    class_group_id: string;
    order: number;
    start_time: string;
    end_time: string;
    duration_minutes?: number;
}

export interface AcademicPeriod {
    id: string;
    tenant_id: string;
    name: string;
    year: number;
    break_type: BreakType;
    start_date: string;
    end_date: string;
    classes_per_day: number;
    is_active: boolean;
    created_at: string;
    updated_at: string;
    period_breaks?: PeriodBreak[];
    non_school_days?: NonSchoolDay[];
    extra_school_days?: ExtraSchoolDay[];
}

export interface AcademicPeriodCreate {
    name: string;
    year: number;
    break_type: BreakType;
    start_date: string;
    end_date: string;
    classes_per_day: number;
    is_active?: boolean;
}

export interface PeriodStatistics {
    period_id: string;
    period_name: string;
    total_days: number;
    school_days: number;
    non_school_days_count: number;
    total_classes_available: number;
    classes_per_day: number;
    schedules_count: number;
    breaks_count: number;
    start_date: string;
    end_date: string;
}
