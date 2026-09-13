import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.core.config import settings
from app.api.v1.api import api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("transformai")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for startup and shutdown routines."""
    logger.info("Starting up TransformAI backend service...")
    logger.info("Environment: %s", settings.ENVIRONMENT)
    logger.info("API prefix: %s", settings.API_V1_STR)

    # Initialize database extensions and tables if accessible
    try:
        from app.core.database import engine, Base
        from sqlalchemy import text
        import app.models  # Ensure all models are imported before creating tables
        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            await conn.run_sync(Base.metadata.create_all)
            logger.info("PostgreSQL pgvector extension & database tables verified successfully.")
    except Exception as exc:
        logger.warning("Could not initialize database tables on startup (will retry on health checks): %s", exc)

    yield
    logger.info("Shutting down TransformAI backend service...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Research-Oriented Gen AI Platform for Automated Content Transformation (SIH26154)",
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", include_in_schema=False)
async def root_redirect():
    """Redirects root to Swagger API documentation."""
    return RedirectResponse(url="/docs")
