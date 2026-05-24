"""FastAPI dependency injection from AppContainer."""

from fastapi import Depends, Header, HTTPException, Request, status

from app.application.chat.service import ChatService
from app.application.permissions.service import PermissionService
from app.bootstrap.container import AppContainer, get_container
from app.domain.auth.models import UserContext


def get_app_container(request: Request) -> AppContainer:
    return request.app.state.container


def get_chat_service(container: AppContainer = Depends(get_app_container)) -> ChatService:
    return container.chat_service()


def get_permission_service(
    container: AppContainer = Depends(get_app_container),
) -> PermissionService:
    return container.permission_service()


async def get_auth_token(request: Request) -> str:
    """Return token from middleware state or Authorization header."""
    if token := getattr(request.state, "token", None):
        return token
    return await _parse_auth_header(request.headers.get("Authorization"))


async def get_current_user(request: Request) -> UserContext:
    """Return UserContext attached by IAMAuthMiddleware."""
    user = getattr(request.state, "user", None)
    if user is not None:
        return user
    token = await get_auth_token(request)
    container = get_app_container(request)
    return await container.permission_service().resolve_user_context(token)


async def _parse_auth_header(authorization: str | None) -> str:
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
