"""
Database module — async SQLAlchemy engine, session factory, and table creation.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

# ── Engine & Session ──────────────────────────────────────────────────────────

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
)

async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── Base Model ────────────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    """Declarative base for all ORM models."""
    pass


# ── Dependency ────────────────────────────────────────────────────────────────

async def get_db() -> AsyncSession:
    """FastAPI dependency that yields an async database session."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ── Init ──────────────────────────────────────────────────────────────────────

async def init_db():
    """Database startup logic. Tables are now managed by Alembic."""
    pass
