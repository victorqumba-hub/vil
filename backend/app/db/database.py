"""SQLAlchemy async engine and session factory."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

import logging
import asyncio

logger = logging.getLogger(__name__)

def get_engine_url():
    """Determine the best database URL to use."""
    # In a real environment, we might try to ping the PG port here, 
    # but for simplicity we'll rely on the startup script setting 
    # the environment or checking the URL.
    return settings.DATABASE_URL

connect_args = {}
engine_kwargs = {
    "echo": settings.DEBUG,
}

actual_url = get_engine_url()

if "sqlite" in actual_url:
    connect_args["check_same_thread"] = False
else:
    engine_kwargs["pool_size"] = 20
    engine_kwargs["max_overflow"] = 10

engine = create_async_engine(
    actual_url,
    connect_args=connect_args,
    **engine_kwargs,
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""
    pass


async def get_db() -> AsyncSession:  # type: ignore[misc]
    """FastAPI dependency — yields an async DB session."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Create all tables (dev convenience — use Alembic in production)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
