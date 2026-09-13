from fastapi import APIRouter, status
from app.core.config import settings
from app.core.database import check_database_connection
from app.core.redis import check_redis_connection
from app.schemas.health import (
    HealthResponse,
    SystemHealthResponse,
    DatabaseHealth,
    RedisHealth,
)

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Basic API Liveness Health Check",
    description="Returns basic application status and metadata to verify the API process is alive.",
)
async def get_health() -> HealthResponse:
    """Liveness probe."""
    return HealthResponse(
        status="healthy",
        app_name=settings.PROJECT_NAME,
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
    )


@router.get(
    "/health/system",
    response_model=SystemHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Deep System Readiness & Diagnostics",
    description="Tests live connectivity to PostgreSQL database (including pgvector check) and Redis cache.",
)
async def get_system_health() -> SystemHealthResponse:
    """Readiness probe checking PostgreSQL and Redis dependencies."""
    db_result = await check_database_connection()
    redis_result = await check_redis_connection()

    db_health = DatabaseHealth(**db_result)
    redis_health = RedisHealth(**redis_result)

    overall_status = (
        "healthy"
        if (db_health.connected and redis_health.connected)
        else "degraded"
    )

    return SystemHealthResponse(
        status=overall_status,
        app_name=settings.PROJECT_NAME,
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        database=db_health,
        redis=redis_health,
    )
