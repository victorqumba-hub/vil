"""SQLAlchemy async engine and session factory."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

import logging
import asyncio

logger = logging.getLogger(__name__)

def get_engine_url():
    """Determine the best database URL to use."""
    url = settings.DATABASE_URL
    
    # Auto-fix for Supabase Transaction Pooler (port 6543):
    # asyncpg uses prepared statements by default, but Supabase's
    # transaction pooler does NOT support them. This causes cryptic
    # "Tenant or user not found" errors. We auto-append the fix.
    if "supabase" in url and "prepared_statement_cache_size" not in url:
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}prepared_statement_cache_size=0"
        logger.info("[DB] Auto-applied prepared_statement_cache_size=0 for Supabase Pooler")
    
    return url

def create_vil_engine():
    """Create a new engine based on current settings/env."""
    url = get_engine_url()
    
    _connect_args = {}
    _engine_kwargs = {
        "echo": settings.DEBUG,
    }

    if "sqlite" in url:
        _connect_args["check_same_thread"] = False
    else:
        # Keep pool small for free-tier cloud instances
        _engine_kwargs["pool_size"] = 5
        _engine_kwargs["max_overflow"] = 3
        _engine_kwargs["pool_pre_ping"] = True
        
        # Critical fix for Supabase Transaction Pooler (port 6543):
        # asyncpg uses prepared statements by default, but Supabase's
        # transaction pooler does NOT support them. The fix MUST be
        # passed via connect_args, not as a URL parameter.
        if "supabase" in url or ":6543" in url:
            _connect_args["statement_cache_size"] = 0
            _connect_args["prepared_statement_cache_size"] = 0
            logger.info("[DB] Applied statement_cache_size=0 for Supabase Transaction Pooler")

    return create_async_engine(
        url,
        connect_args=_connect_args,
        **_engine_kwargs,
    )


engine = create_vil_engine()

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
