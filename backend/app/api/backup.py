from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import datetime, date, time
import json
from enum import Enum

from app.database import get_db
from app.models.tenant import Tenant
from app.models.user import User
from app.models.course import Course, Subject, CurriculumMatrix, MatrixSubject
from app.models.academic_period import AcademicPeriod, PeriodBreak, NonSchoolDay, ExtraSchoolDay
from app.models.class_group import ClassGroup, ClassGroupStudent, ClassGroupStudentSubject
from app.models.content import LessonPlan
from app.models.academic import Enrollment, Grade, Attendance, enrollment_period_breaks
from app.auth.dependencies import require_role
from app.models.user import UserRole
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/backup", tags=["backup"])

class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, time):
            return obj.strftime('%H:%M:%S')
        if isinstance(obj, Enum):
            return obj.value
        return super().default(obj)

def row2dict(row):
    d = {}
    for column in row.__table__.columns:
        val = getattr(row, column.name)
        d[column.name] = val
    return d

@router.get("/tenants/{tenant_id}/export")
async def export_tenant(
    tenant_id: UUID, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN))
):
    # Fetch Tenant
    res = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = res.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
        
    data = {"tenant": row2dict(tenant)}
    
    # Users
    res = await db.execute(select(User).where(User.tenant_id == tenant_id))
    data["users"] = [row2dict(u) for u in res.scalars().all()]
    
    # Subjects
    res = await db.execute(select(Subject).where(Subject.tenant_id == tenant_id))
    data["subjects"] = [row2dict(s) for s in res.scalars().all()]
    
    # Courses
    res = await db.execute(select(Course).where(Course.tenant_id == tenant_id))
    data["courses"] = [row2dict(c) for c in res.scalars().all()]
    
    # Academic Periods
    res = await db.execute(select(AcademicPeriod).where(AcademicPeriod.tenant_id == tenant_id))
    periods = res.scalars().all()
    data["academic_periods"] = [row2dict(p) for p in periods]
    period_ids = [p.id for p in periods]
    
    # Period Breaks, NonSchoolDay, ExtraSchoolDay
    if period_ids:
        res = await db.execute(select(PeriodBreak).where(PeriodBreak.academic_period_id.in_(period_ids)))
        data["period_breaks"] = [row2dict(pb) for pb in res.scalars().all()]
        
        res = await db.execute(select(NonSchoolDay).where(NonSchoolDay.academic_period_id.in_(period_ids)))
        data["non_school_days"] = [row2dict(ns) for ns in res.scalars().all()]
        
        res = await db.execute(select(ExtraSchoolDay).where(ExtraSchoolDay.academic_period_id.in_(period_ids)))
        data["extra_school_days"] = [row2dict(es) for es in res.scalars().all()]
    else:
        data["period_breaks"] = []
        data["non_school_days"] = []
        data["extra_school_days"] = []

    # Curriculum Matrices
    course_ids = [c["id"] for c in data["courses"]]
    if course_ids:
        res = await db.execute(select(CurriculumMatrix).where(CurriculumMatrix.course_id.in_(course_ids)))
        matrices = res.scalars().all()
        data["curriculum_matrices"] = [row2dict(m) for m in matrices]
        matrix_ids = [m.id for m in matrices]
        
        if matrix_ids:
            res = await db.execute(select(MatrixSubject).where(MatrixSubject.matrix_id.in_(matrix_ids)))
            matrix_subjects = res.scalars().all()
            data["matrix_subjects"] = [row2dict(ms) for ms in matrix_subjects]
            matrix_subject_ids = [ms.id for ms in matrix_subjects]
        else:
            data["matrix_subjects"] = []
            matrix_subject_ids = []
    else:
        data["curriculum_matrices"] = []
        data["matrix_subjects"] = []
        matrix_subject_ids = []

    # Class Groups
    if course_ids and period_ids:
        res = await db.execute(select(ClassGroup).where(ClassGroup.course_id.in_(course_ids), ClassGroup.academic_period_id.in_(period_ids)))
        class_groups = res.scalars().all()
        data["class_groups"] = [row2dict(cg) for cg in class_groups]
        class_group_ids = [cg.id for cg in class_groups]
        
        if class_group_ids:
            res = await db.execute(select(ClassGroupStudent).where(ClassGroupStudent.class_group_id.in_(class_group_ids)))
            data["class_group_students"] = [row2dict(cgs) for cgs in res.scalars().all()]
            
            res = await db.execute(select(ClassGroupStudentSubject).where(ClassGroupStudentSubject.class_group_id.in_(class_group_ids)))
            data["class_group_student_subjects"] = [row2dict(cgss) for cgss in res.scalars().all()]
        else:
            data["class_group_students"] = []
            data["class_group_student_subjects"] = []
    else:
        data["class_groups"] = []
        data["class_group_students"] = []
        data["class_group_student_subjects"] = []

    # Lesson Plans
    if matrix_subject_ids:
        res = await db.execute(select(LessonPlan).where(LessonPlan.matrix_subject_id.in_(matrix_subject_ids)))
        lesson_plans = res.scalars().all()
        data["lesson_plans"] = [row2dict(lp) for lp in lesson_plans]
        lesson_plan_ids = [lp.id for lp in lesson_plans]
        
    else:
        data["lesson_plans"] = []
        lesson_plan_ids = []

    # Enrollments
    user_ids = [u["id"] for u in data["users"]]
    if user_ids and course_ids:
        res = await db.execute(select(Enrollment).where(Enrollment.student_id.in_(user_ids), Enrollment.course_id.in_(course_ids)))
        enrollments = res.scalars().all()
        data["enrollments"] = [row2dict(e) for e in enrollments]
        enrollment_ids = [e.id for e in enrollments]
        
        if enrollment_ids:
            res = await db.execute(select(enrollment_period_breaks).where(enrollment_period_breaks.c.enrollment_id.in_(enrollment_ids)))
            data["enrollment_period_breaks"] = [{"enrollment_id": str(row.enrollment_id), "period_break_id": str(row.period_break_id)} for row in res.all()]
            
            res = await db.execute(select(Grade).where(Grade.enrollment_id.in_(enrollment_ids)))
            data["grades"] = [row2dict(g) for g in res.scalars().all()]
            
            res = await db.execute(select(Attendance).where(Attendance.enrollment_id.in_(enrollment_ids)))
            data["attendances"] = [row2dict(a) for a in res.scalars().all()]
        else:
            data["enrollment_period_breaks"] = []
            data["grades"] = []
            data["attendances"] = []
    else:
        data["enrollments"] = []
        data["enrollment_period_breaks"] = []
        data["grades"] = []
        data["attendances"] = []

    content = json.loads(json.dumps(data, cls=CustomEncoder))
    return JSONResponse(content=content)


def convert_types(model_class, d):
    valid_keys = {}
    for c in model_class.__table__.columns:
        valid_keys[c.name] = c
    
    filtered = {}
    for k, v in d.items():
        if k in valid_keys and v is not None:
            col = valid_keys[k]
            ctype = str(col.type).upper()
            if 'DATETIME' in ctype or 'TIMESTAMP' in ctype:
                try:
                    if isinstance(v, str):
                        filtered[k] = datetime.fromisoformat(v.replace("Z", "+00:00"))
                except:
                    filtered[k] = v
            elif 'DATE' in ctype:
                try:
                    if isinstance(v, str):
                        filtered[k] = date.fromisoformat(v)
                except:
                    filtered[k] = v
            elif 'TIME' in ctype:
                try:
                    if isinstance(v, str):
                        filtered[k] = time.fromisoformat(v)
                except:
                    filtered[k] = v
            else:
                filtered[k] = v
    return filtered

@router.post("/tenants/import")
async def import_tenant(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN))
):
    content = await file.read()
    try:
        data = json.loads(content)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON file")
        
    order = [
        (Tenant, "tenant", True),
        (User, "users", False),
        (Subject, "subjects", False),
        (Course, "courses", False),
        (AcademicPeriod, "academic_periods", False),
        (PeriodBreak, "period_breaks", False),
        (NonSchoolDay, "non_school_days", False),
        (ExtraSchoolDay, "extra_school_days", False),
        (CurriculumMatrix, "curriculum_matrices", False),
        (MatrixSubject, "matrix_subjects", False),
        (ClassGroup, "class_groups", False),
        (ClassGroupStudent, "class_group_students", False),
        (ClassGroupStudentSubject, "class_group_student_subjects", False),
        (LessonPlan, "lesson_plans", False),
        (Enrollment, "enrollments", False),
        (Grade, "grades", False),
        (Attendance, "attendances", False),
    ]

    try:
        for model_class, key, is_single in order:
            if key not in data: continue
            
            items = [data[key]] if is_single else data[key]
            
            for item in items:
                filtered = convert_types(model_class, item)
                
                if "id" in filtered:
                    res = await db.execute(select(model_class).where(model_class.id == filtered["id"]))
                    existing = res.scalar_one_or_none()
                    if existing:
                        for k, v in filtered.items():
                            if k != "id":
                                setattr(existing, k, v)
                    else:
                        db.add(model_class(**filtered))
                else:
                    db.add(model_class(**filtered))
                    
        # Many to many table: enrollment_period_breaks
        if "enrollment_period_breaks" in data:
            for epb in data["enrollment_period_breaks"]:
                res = await db.execute(select(enrollment_period_breaks).where(
                    enrollment_period_breaks.c.enrollment_id == epb["enrollment_id"],
                    enrollment_period_breaks.c.period_break_id == epb["period_break_id"]
                ))
                if not res.first():
                    await db.execute(enrollment_period_breaks.insert().values(
                        enrollment_id=epb["enrollment_id"], 
                        period_break_id=epb["period_break_id"]
                    ))

        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error importing: {str(e)}")

    return {"detail": "Import successful"}
