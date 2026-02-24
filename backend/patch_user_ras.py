import asyncio
import os
import sys

# Add backend directory to sys.path so 'app' can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import AsyncSessionLocal
from app.models.user import User, UserRole
from app.core.registration import generate_registration_number
from sqlalchemy import select

async def backfill_ras():
    print("Iniciando atualização de RAs para usuários existentes...")
    async with AsyncSessionLocal() as db:
        # Obter todos os usuários, ordenados por data de criação para manter a sequência original
        result = await db.execute(select(User).order_by(User.created_at))
        users = result.scalars().all()
        
        updated_count = 0
        for user in users:
            # Force update all existing to ensure no duplicates
            
            # Gerar novo RA
            year = user.created_at.year if user.created_at else 2026
            new_ra = await generate_registration_number(db, user.role, user.tenant_id, year)
            print(f"Atualizando {user.email} (Role: {user.role.value}): {user.registration_number} -> {new_ra}")
            user.registration_number = new_ra
            await db.commit()  # <--- COMMIT AQUI PARA GARANTIR VERIFICAÇÃO DE COLISÃO
            updated_count += 1
                
        print(f"Sucesso! {updated_count} usuários foram atualizados com o novo formato de RA.")

if __name__ == "__main__":
    asyncio.run(backfill_ras())
