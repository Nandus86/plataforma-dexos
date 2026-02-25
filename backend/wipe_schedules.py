import asyncio
from sqlalchemy import text
from app.database import async_session_maker

async def wipe():
    async with async_session_maker() as db:
        await db.execute(text('TRUNCATE TABLE class_schedules CASCADE;'))
        await db.commit()
    print('Schedules wiped')

if __name__ == "__main__":
    asyncio.run(wipe())
