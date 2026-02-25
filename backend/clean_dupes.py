import asyncio
from app.database import AsyncSessionLocal
from sqlalchemy import text

async def clean():
    async with AsyncSessionLocal() as session:
        await session.execute(text('DELETE FROM class_schedules WHERE id IN (SELECT id FROM (SELECT id, ROW_NUMBER() OVER (partition BY class_group_id, "order" ORDER BY id) as rnum FROM class_schedules) t WHERE t.rnum > 1);'))
        await session.commit()
        print("Duplicates removed.")

if __name__ == "__main__":
    asyncio.run(clean())
