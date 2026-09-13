from typing import AsyncGenerator, Dict, Any
import time
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

from app.core.config import settings

# Async Engine and Session
engine = create_async_engine(
    settings.async_database_url,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for obtaining an asynchronous database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def check_database_connection() -> Dict[str, Any]:
    """
    Executes a live query to verify PostgreSQL connectivity
    and tests for pgvector extension presence.
    """
    start_time = time.perf_counter()
    try:
        async with engine.connect() as conn:
            # Check basic connectivity
            result = await conn.execute(text("SELECT 1;"))
            result.scalar()

            # Check for pgvector extension
            vector_res = await conn.execute(
                text("SELECT extversion FROM pg_extension WHERE extname = 'vector';")
            )
            vector_version = vector_res.scalar()

            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return {
                "status": "healthy",
                "connected": True,
                "latency_ms": latency_ms,
                "pgvector_installed": vector_version is not None,
                "pgvector_version": vector_version if vector_version else None,
                "error": None,
            }
    except Exception as e:
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return {
            "status": "unhealthy",
            "connected": False,
            "latency_ms": latency_ms,
            "pgvector_installed": False,
            "pgvector_version": None,
            "error": str(e),
        }
