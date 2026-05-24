"""Health check endpoints."""

from datetime import datetime, timezone

import httpx
from fastapi import APIRouter

from app.core.config import settings
from app.infrastructure.tools.registry import tool_registry

router = APIRouter()


@router.get("/health")
async def health_check() -> dict:
    """Basic liveness probe."""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/health/ready")
async def readiness_check() -> dict:
    """
    Readiness probe — verifies downstream dependencies.

    Returns degraded status if optional dependencies are unreachable.
    """
    checks: dict[str, str] = {"iam": "unknown", "ollama": "unknown"}
    overall = "ready"

    # IAM connectivity
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(f"{settings.iam_service_url}/health")
            checks["iam"] = "up" if response.status_code < 500 else "degraded"
    except httpx.RequestError:
        checks["iam"] = "down"
        overall = "degraded"

    # Ollama connectivity (when using local LLM)
    if settings.llm_provider.value == "ollama":
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{settings.ollama_base_url}/api/tags")
                checks["ollama"] = "up" if response.status_code < 500 else "degraded"
        except httpx.RequestError:
            checks["ollama"] = "down"
            overall = "degraded"
    else:
        checks["ollama"] = "skipped"

    return {
        "status": overall,
        "checks": checks,
        "tools_registered": len(tool_registry.get_all_definitions()),
        "llm_provider": settings.llm_provider.value,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
