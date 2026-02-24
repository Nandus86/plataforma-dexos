import asyncio
from sqlalchemy import text
from app.database import engine

async def reset():
    async with engine.begin() as conn:
        print("Truncating tables...")
        await conn.execute(text("""
            TRUNCATE TABLE 
                lesson_plans, 
                class_group_student_subjects, 
                class_group_students, 
                class_group_subject_professors, 
                class_group_subjects, 
                class_groups, 
                matrix_subjects, 
                curriculum_matrices, 
                subjects, 
                courses 
            CASCADE;
        """))
        print("Done.")

asyncio.run(reset())
