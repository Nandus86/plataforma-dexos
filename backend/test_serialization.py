import asyncio
from app.database import AsyncSessionLocal
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.class_group import ClassGroup
from app.schemas.class_group import ClassGroupDetailResponse

async def check():
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(ClassGroup)
            .options(
                selectinload(ClassGroup.class_schedules)
            )
            .where(ClassGroup.id == '943fd33b-3e14-4094-91ba-c210511ab3aa')
        )
        group = result.scalars().first()
        if group:
            response = ClassGroupDetailResponse(
                id=group.id,
                tenant_id=group.tenant_id,
                course_id=group.course_id,
                name=group.name,
                year=group.year,
                shift=group.shift.value,
                is_active=group.is_active,
                created_at=group.created_at,
                class_schedules=group.class_schedules
            )
            print("DB length:", len(group.class_schedules))
            print("Dict length:", len(response.model_dump().get("class_schedules", [])))

if __name__ == "__main__":
    asyncio.run(check())
