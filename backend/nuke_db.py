import asyncio
from sqlalchemy import select, delete, text
from app.database import AsyncSessionLocal
from app.models.user import User, UserRole
from app.models.tenant import Tenant

async def hard_reset_database():
    async with AsyncSessionLocal() as session:
        print("Starting secure wipe of Exousia Database...")
        superadmin_email = "fernandomskt86@gmail.com"

        # 1. Fetch the superadmin we want to keep
        result = await session.execute(select(User).where(User.email == superadmin_email))
        superadmin = result.scalar_one_or_none()

        if not superadmin:
            print(f"CRITICAL: Production Superadmin ({superadmin_email}) NOT FOUND.")
            print("Please ensure the superadmin is created before wiping!")
            return
            
        # Temporarily detach superadmin from tenant to allow tenant deletion
        superadmin.tenant_id = None
        await session.commit()
            
        # Disable foreign key checks temporarily to avoid circular dependencies
        await session.execute(text("SET session_replication_role = 'replica';"))

        # 2. Delete ALL Tenants First
        await session.execute(delete(Tenant))
        print("Deleted all Tenants and their cascaded school data (Courses, Classes, Enrollments, Schedules, Logs).")

        # 3. Delete ALL users except the specific superadmin (this cascades to some relationships)
        await session.execute(delete(User).where(User.id != superadmin.id))
        print("Deleted all mock/demo Users (students, professors, admins).")
        
        # Restore foreign key checks
        await session.execute(text("SET session_replication_role = 'origin';"))

        await session.commit()
        print("Database wiped and optimized for production deployment.")

if __name__ == "__main__":
    asyncio.run(hard_reset_database())
