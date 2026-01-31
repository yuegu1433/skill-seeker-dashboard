"""Database connection and session management.

This module provides database connection management using
SQLAlchemy with async support.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_timeout=settings.DATABASE_POOL_TIMEOUT,
    pool_recycle=settings.DATABASE_POOL_RECYCLE,
    echo=settings.DEBUG,  # Enable SQL logging in debug mode
    poolclass=NullPool if settings.ENVIRONMENT == "test" else None,
)

# Create session factory
SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=True,
    autocommit=False,
)


async def get_db_session() -> AsyncSession:
    """Dependency injection for database sessions.

    Yields:
        AsyncSession: Database session
    """
    async with SessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


async def create_db_session() -> AsyncSession:
    """Create a new database session.

    Returns:
        AsyncSession: Database session
    """
    return SessionLocal()


async def init_db():
    """Initialize database connection."""
    logger.info("Initializing database connection...")
    try:
        # Test the connection
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
        logger.info("Database connection successful")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise


async def close_db():
    """Close database connection."""
    logger.info("Closing database connection...")
    await engine.dispose()
    logger.info("Database connection closed")
