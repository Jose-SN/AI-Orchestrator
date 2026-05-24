"""IAM authentication middleware — validates JWT and attaches user context."""

from collections.abc import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.exceptions import AuthenticationError, AuthorizationError, IAMServiceError
from app.core.logging import AuditAction, audit_log, get_logger
from app.infrastructure.iam.client import IAMClient

logger = get_logger(__name__)

PUBLIC_PATHS = {"/api/v1/health", "/api/v1/health/ready", "/docs", "/redoc", "/openapi.json"}


class IAMAuthMiddleware(BaseHTTPMiddleware):
    """Validates JWT via IAM and attaches UserContext to request.state."""

    def __init__(self, app, iam_client: IAMClient | None = None) -> None:
        super().__init__(app)
        self._default_iam = iam_client

    def _resolve_iam(self, request: Request) -> IAMClient:
        container = getattr(request.app.state, "container", None)
        if container is not None:
            return container.iam_client()
        return self._default_iam or IAMClient()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.url.path in PUBLIC_PATHS or request.method == "OPTIONS":
            return await call_next(request)

        token = _extract_bearer_token(request)
        if not token:
            return JSONResponse(
                status_code=401,
                content={"error": "AUTHENTICATION_ERROR", "message": "Missing Authorization header"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        iam = self._resolve_iam(request)
        try:
            user = await iam.resolve_user_context(token)
            request.state.token = token
            request.state.user = user
            logger.debug("iam_auth_success", user_id=user.user_id, path=request.url.path)
        except AuthenticationError as exc:
            audit_log(AuditAction.AUTH_FAILURE, outcome="invalid_token", metadata={"path": request.url.path})
            return JSONResponse(
                status_code=401,
                content={"error": exc.code, "message": exc.message},
                headers={"WWW-Authenticate": "Bearer"},
            )
        except AuthorizationError as exc:
            return JSONResponse(status_code=403, content={"error": exc.code, "message": exc.message})
        except IAMServiceError as exc:
            logger.error("iam_middleware_error", message=exc.message)
            return JSONResponse(status_code=502, content={"error": exc.code, "message": exc.message})

        return await call_next(request)


def _extract_bearer_token(request: Request) -> str | None:
    auth = request.headers.get("Authorization")
    if not auth:
        return None
    parts = auth.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1]
