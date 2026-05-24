"""IAM service HTTP client — authentication and permission resolution."""

from typing import Any

import httpx

from app.core.config import settings
from app.core.exceptions import AuthenticationError, AuthorizationError, IAMServiceError
from app.core.logging import get_logger
from app.domain.models.permission import UserContext
from app.infrastructure.http.base_client import BaseHTTPClient

logger = get_logger(__name__)


class IAMClient(BaseHTTPClient):
    """Client for the IAM microservice — sole authority on auth and permissions."""

    def __init__(self) -> None:
        super().__init__(
            base_url=settings.iam_service_url,
            service_name="iam-service",
            timeout_seconds=settings.iam_timeout_seconds,
        )

    async def validate_token(self, token: str) -> dict[str, Any]:
        """Validate a JWT token with the IAM service."""
        try:
            client = await self._get_client()
            response = await client.post(
                settings.iam_validate_token_path,
                headers={"Authorization": f"Bearer {token}"},
            )
            if response.status_code == 401:
                raise AuthenticationError("Invalid or expired token")
            response.raise_for_status()
            return response.json()
        except AuthenticationError:
            raise
        except httpx.HTTPStatusError as exc:
            raise IAMServiceError(
                f"Token validation failed: HTTP {exc.response.status_code}"
            ) from exc
        except httpx.RequestError as exc:
            raise IAMServiceError(f"IAM service unreachable: {exc}") from exc

    async def get_user_permissions(self, token: str) -> UserContext:
        """Fetch user identity and permissions from IAM."""
        try:
            client = await self._get_client()
            response = await client.get(
                settings.iam_permissions_path,
                headers={"Authorization": f"Bearer {token}"},
            )
            if response.status_code == 401:
                raise AuthenticationError("Invalid or expired token")
            if response.status_code == 403:
                raise AuthorizationError("Access denied")
            response.raise_for_status()
            data = response.json()

            return UserContext(
                user_id=str(data.get("userId") or data.get("user_id") or data.get("id", "")),
                email=data.get("email"),
                display_name=data.get("displayName") or data.get("display_name"),
                roles=data.get("roles", []),
                permissions=data.get("permissions", []),
                module_permissions=data.get("modulePermissions")
                or data.get("module_permissions", []),
            )
        except (AuthenticationError, AuthorizationError):
            raise
        except httpx.HTTPStatusError as exc:
            raise IAMServiceError(
                f"Permission lookup failed: HTTP {exc.response.status_code}"
            ) from exc
        except httpx.RequestError as exc:
            raise IAMServiceError(f"IAM service unreachable: {exc}") from exc
