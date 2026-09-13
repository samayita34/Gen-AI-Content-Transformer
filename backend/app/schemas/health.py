from typing import Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(..., examples=["healthy"])
    app_name: str = Field(..., examples=["TransformAI"])
    version: str = Field(..., examples=["0.1.0"])
    environment: str = Field(..., examples=["development"])


class DatabaseHealth(BaseModel):
    status: str = Field(..., examples=["healthy"])
    connected: bool = Field(..., examples=[True])
    latency_ms: Optional[float] = Field(None, examples=[2.15])
    pgvector_installed: bool = Field(..., examples=[True])
    pgvector_version: Optional[str] = Field(None, examples=["0.7.0"])
    error: Optional[str] = Field(None)


class RedisHealth(BaseModel):
    status: str = Field(..., examples=["healthy"])
    connected: bool = Field(..., examples=[True])
    latency_ms: Optional[float] = Field(None, examples=[0.85])
    error: Optional[str] = Field(None)


class SystemHealthResponse(BaseModel):
    status: str = Field(..., examples=["healthy"])
    app_name: str = Field(..., examples=["TransformAI"])
    version: str = Field(..., examples=["0.1.0"])
    environment: str = Field(..., examples=["development"])
    database: DatabaseHealth
    redis: RedisHealth
