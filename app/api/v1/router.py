"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1.endpoints import chat, health

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(health.router, tags=["Health"])
api_v1_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
