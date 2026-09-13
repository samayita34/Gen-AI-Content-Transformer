from fastapi import APIRouter
from app.api.v1.endpoints import health, documents, retrieval

api_router = APIRouter()

# Register endpoints
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_router.include_router(retrieval.router, prefix="/retrieval", tags=["Retrieval"])

