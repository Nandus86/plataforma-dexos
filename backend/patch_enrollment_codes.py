import asyncio
import os
import sys

# Add backend directory to sys.path so 'app' can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import AsyncSessionLocal
from app.models.academic import Enrollment
from app.models.user import User
from app.models.academic_period import AcademicPeriod
from sqlalchemy import select

async def backfill_enrollments():
    print("Iniciando atualização de Códigos de Matrícula para matrículas existentes...")
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Enrollment))
        enrollments = result.scalars().all()
        
        from app.core.registration import generate_enrollment_code

        updated_count = 0
        for e in enrollments:
            # Check if misses or needs overwrite
            # Fetch student and period
            # Ensure student and academic_period are loaded for the enrollment object
            # This might require eager loading or explicit loading if not already available
            await db.refresh(e, attribute_names=['student', 'academic_period'])

            student = e.student
            period = e.academic_period

            if not student or not period or not student.registration_number:
                print(f"Ignorando matrícula {e.id}: falta aluno, período ou RA")
                continue

            expected_code = await generate_enrollment_code(db, student.registration_number, period.year)
            if e.enrollment_code != expected_code:
                # We need to manually construct here without saving it first, or use the generator
                print(f"Atualizando código de matrícula: {e.id} -> {expected_code}")
                e.enrollment_code = expected_code
                await db.commit() # Commit inside to check collision for next iteration
                updated_count += 1
                
        if updated_count > 0:
            # The final commit is not strictly necessary if we commit inside the loop,
            # but it doesn't hurt and ensures any final changes are saved.
            # However, the instruction implies committing inside the loop for unicity checks.
            # Let's keep the final commit for robustness if any other changes were made.
            await db.commit() 
            print(f"Sucesso! {updated_count} matrículas foram atualizadas com o novo formato.")
        else:
            print("Todas as matrículas já estão corretas ou não há o que atualizar.")

if __name__ == "__main__":
    asyncio.run(backfill_enrollments())
