import asyncio
from app.database import AsyncSessionLocal
from app.models.user import User, UserRole
from app.auth.security import hash_password

from sqlalchemy import select, delete

async def create_superadmin():
    async with AsyncSessionLocal() as session:
        # Delete any existing duplicates first
        await session.execute(delete(User).where(User.email == 'fernandomskt86@gmail.com'))
        await session.commit()
        
        # Create fresh unique super admin
        pwd = hash_password('fernando123')
        sa = User(
            email='fernandomskt86@gmail.com',
            password_hash=pwd,
            name='Fernando Super Admin',
            role=UserRole.SUPERADMIN,
            is_active=True
        )
        session.add(sa)
        await session.commit()
        print('Superadmin deleted duplicates and recreated cleanly!')

if __name__ == "__main__":
    asyncio.run(create_superadmin())
