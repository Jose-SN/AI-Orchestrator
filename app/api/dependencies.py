"""FastAPI dependencies and DI wiring."""

from functools import lru_cache

from fastapi import Depends, Header, HTTPException, status

from app.agents.orchestrator_agent import OrchestratorAgent
from app.application.services.chat_service import ChatService
from app.application.services.permission_service import PermissionService
from app.infrastructure.http.iam_client import IAMClient
from app.infrastructure.http.microservice_client import MicroserviceClientFactory


@lru_cache
def get_iam_client() -> IAMClient:
    return IAMClient()


@lru_cache
def get_microservice_factory() -> MicroserviceClientFactory:
    return MicroserviceClientFactory()


@lru_cache
def get_orchestrator_agent() -> OrchestratorAgent:
    return OrchestratorAgent()


def get_permission_service(
    iam_client: IAMClient = Depends(get_iam_client),
) -> PermissionService:
    return PermissionService(iam_client)


def get_chat_service(
    permission_service: PermissionService = Depends(get_permission_service),
    agent: OrchestratorAgent = Depends(get_orchestrator_agent),
) -> ChatService:
    return ChatService(permission_service=permission_service, agent=agent)


async def get_auth_token(authorization: str | None = Header(default=None)) -> str:
    """Extract Bearer token from Authorization header."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Expected: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return parts[1]
