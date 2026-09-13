from typing import AsyncGenerator, Dict, Any
import time
import redis.asyncio as aioredis
from app.core.config import settings

# Global redis client connection pool
redis_pool = aioredis.ConnectionPool.from_url(
    settings.async_redis_url,
    decode_responses=True,
    max_connections=20,
)


def get_redis_client() -> aioredis.Redis:
    """Returns an async Redis client."""
    return aioredis.Redis(connection_pool=redis_pool)


async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    """FastAPI Dependency for obtaining an async Redis connection."""
    client = get_redis_client()
    try:
        yield client
    finally:
        await client.aclose()


async def check_redis_connection() -> Dict[str, Any]:
    """
    Executes a live PING command to verify Redis connectivity.
    """
    start_time = time.perf_counter()
    client = get_redis_client()
    try:
        pong = await client.ping()
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return {
            "status": "healthy" if pong else "unhealthy",
            "connected": bool(pong),
            "latency_ms": latency_ms,
            "error": None,
        }
    except Exception as e:
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return {
            "status": "unhealthy",
            "connected": False,
            "latency_ms": latency_ms,
            "error": str(e),
        }
    finally:
        await client.aclose()
