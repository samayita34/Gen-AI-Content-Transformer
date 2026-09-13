import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_redirect(async_client: AsyncClient):
    """Verifies root endpoint redirects to /docs."""
    response = await async_client.get("/", follow_redirects=False)
    assert response.status_code in (302, 307)
    assert response.headers["location"] == "/docs"


@pytest.mark.asyncio
async def test_openapi_schema(async_client: AsyncClient):
    """Verifies OpenAPI schema is accessible."""
    response = await async_client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "paths" in data
    assert "/api/v1/health" in data["paths"]
    assert "/api/v1/health/system" in data["paths"]


@pytest.mark.asyncio
async def test_liveness_health_endpoint(async_client: AsyncClient):
    """Verifies GET /api/v1/health returns expected status and metadata."""
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app_name"] == "TransformAI"
    assert "version" in data
    assert "environment" in data


@pytest.mark.asyncio
async def test_system_health_endpoint_schema(async_client: AsyncClient):
    """
    Verifies GET /api/v1/health/system returns schema with database and redis diagnostics.
    Even if offline during unit testing without live services, the response must conform to schema.
    """
    response = await async_client.get("/api/v1/health/system")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "redis" in data
    assert "connected" in data["database"]
    assert "pgvector_installed" in data["database"]
    assert "connected" in data["redis"]
