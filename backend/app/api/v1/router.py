"""API v1 Router aggregation."""
from fastapi import APIRouter
from app.api.v1.search import router as search_router
from app.api.v1.platforms import router as platforms_router
from app.api.v1.history import router as history_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(search_router)
api_v1_router.include_router(platforms_router)
api_v1_router.include_router(history_router)

__all__ = ["api_v1_router"]
