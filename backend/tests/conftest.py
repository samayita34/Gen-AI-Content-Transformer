import os
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.ext.compiler import compiles
from pgvector.sqlalchemy import Vector

# Set testing environment variable
os.environ["TRANSFORMAI_TESTING"] = "1"

from app.core.database import Base, get_db
import app.models  # load all models
from app.main import app

# Compile pgvector Vector type as JSON for SQLite test engine
@compiles(Vector, "sqlite")
def compile_vector_sqlite(type_, compiler, **kw):
    return "JSON"


# Use a local test SQLite DB
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_transformai.db"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True,
)

TestAsyncSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_database():
    """Initializes test database schema."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()
    if os.path.exists("./test_transformai.db"):
        try:
            os.remove("./test_transformai.db")
        except Exception:
            pass


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency override providing isolated test database sessions."""
    async with TestAsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Provides an async HTTP test client with database override."""
    app.dependency_overrides[get_db] = override_get_db

    # Also override AsyncSessionLocal in documents endpoint for background tasks
    import app.api.v1.endpoints.documents as docs_endpoint
    original_session_local = docs_endpoint.AsyncSessionLocal
    docs_endpoint.AsyncSessionLocal = TestAsyncSessionLocal

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client

    docs_endpoint.AsyncSessionLocal = original_session_local
    app.dependency_overrides.clear()
