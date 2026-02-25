"""
Exousía School by Dexos - Main FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.database import engine, Base
from app.models import *  # noqa: F401, F403 - Import all models for table creation
from app.api import health, auth, tenants, users, courses, academic, assignments, occurrences, content, dashboard, export, class_groups, academic_periods, lesson_plans, attendance_api, grades_api, students, professionals, institution
from app.redis_client import redis_client
from app.seed import seed_initial_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    import asyncio
    import logging
    
    logger = logging.getLogger(__name__)
    
    max_retries = 5
    retry_delay = 5  # seconds
    
    for attempt in range(max_retries):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            break
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Database connection failed. Retrying in {retry_delay}s... (Attempt {attempt + 1}/{max_retries})")
                logger.warning(f"Error: {e}")
                await asyncio.sleep(retry_delay)
            else:
                logger.error("Could not connect to the database after multiple attempts.")
                raise e
                
    await redis_client.connect()
    try:
        await seed_initial_data()
    except Exception as e:
        logger.error(f"Failed to seed initial data: {e}")
        
    yield
    # Shutdown
    await redis_client.disconnect()
    await engine.dispose()


import os

def get_app_version():
    try:
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        version_file = os.path.join(current_dir, "VERSION")
        with open(version_file, "r") as f:
            return f.read().strip()
    except Exception:
        return "1.0.0"

app_version = get_app_version()

app = FastAPI(
    title="Exousía School by Dexos",
    description="Plataforma de Gestão Educacional - API RESTful",
    version=app_version,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router, tags=["Health"])
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(tenants.router, prefix="/tenants", tags=["Tenants"])
app.include_router(institution.router, prefix="/institution", tags=["Institution"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(students.router, prefix="/students", tags=["Students"])
app.include_router(professionals.router, prefix="/professionals", tags=["Professionals"])
app.include_router(courses.router, prefix="/courses", tags=["Courses"])
app.include_router(academic.router, prefix="/academic", tags=["Academic"])
app.include_router(assignments.router, prefix="/assignments", tags=["Assignments"])
app.include_router(occurrences.router, prefix="/occurrences", tags=["Occurrences"])
app.include_router(content.router, prefix="/content", tags=["Content"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(export.router, prefix="/export", tags=["Export"])
app.include_router(class_groups.router, prefix="/class-groups", tags=["Class Groups"])
app.include_router(academic_periods.router, prefix="/academic-periods", tags=["Academic Periods"])
app.include_router(lesson_plans.router, prefix="/lesson-plans", tags=["Lesson Plans"])
app.include_router(attendance_api.router, prefix="/attendance", tags=["Attendance"])
app.include_router(grades_api.router, prefix="/grades", tags=["Grades"])


@app.get("/")
async def root():
    return {
        "name": "Exousía School by Dexos",
        "version": app_version,
        "status": "running",
        "docs": "/docs",
    }

