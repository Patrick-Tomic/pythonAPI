from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Application
from app.schemas import ApplicationCreate, ApplicationUpdate


async def create_application(db: AsyncSession, application: ApplicationCreate) -> Application:
    db_app = Application(**application.model_dump())
    db.add(db_app)
    await db.commit()
    await db.refresh(db_app)
    return db_app


async def get_application(db: AsyncSession, application_id: int) -> Application | None:
    result = await db.execute(select(Application).where(Application.id == application_id))
    return result.scalar_one_or_none()


async def get_applications(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[Application]:
    result = await db.execute(
        select(Application).offset(skip).limit(limit).order_by(Application.id)
    )
    return list(result.scalars().all())


async def update_application(
    db: AsyncSession, application_id: int, application: ApplicationUpdate
) -> Application | None:
    db_app = await get_application(db, application_id)
    if db_app is None:
        return None
    for field, value in application.model_dump(exclude_unset=True).items():
        setattr(db_app, field, value)
    await db.commit()
    await db.refresh(db_app)
    return db_app


async def delete_application(db: AsyncSession, application_id: int) -> bool:
    db_app = await get_application(db, application_id)
    if db_app is None:
        return False
    await db.delete(db_app)
    await db.commit()
    return True