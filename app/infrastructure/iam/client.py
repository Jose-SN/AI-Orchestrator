"""Production IAM integration client — async, retries, caching, structured errors."""

from typing import Any

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.exceptions import AuthenticationError, AuthorizationError, IAMServiceError
from app.core.logging import get_logger
from app.domain.auth.models import IAMUserProfile, ModuleAccess, UserContext
from app.infrastructure.iam.cache import IAMPermissionCache
from app.infrastructure.iam.schemas import TokenValidationResult, parse_iam_profile

logger = get_logger(__name__)


class IAMClient:
    """Client for the IAM microservice — sole authority on auth and permissions."""

    def __init__(
        self,
        *,
        cache: IAMPermissionCache | None = None,
        timeout_seconds: int | None = None,
    ) -> None:
        self._base_url = settings.iam_service_url.rstrip("/")
        self._timeout = httpx.Timeout(timeout_seconds or settings.iam_timeout_seconds)
        self._cache = cache or IAMPermissionCache(ttl_seconds=settings.iam_cache_ttl_seconds)
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=self._timeout,
                headers={"Accept": "application/json", "Content-Type": "application/json"},
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, max=4),
        retry=retry_if_exception_type(IAMServiceError),
        reraise=True,
    )
    async def _request(
        self,
        method: str,
        path: str,
        *,
        token: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        client = await self._get_client()
        url = path if path.startswith("/") else f"/{path}"

        try:
            response = await client.request(
                method=method,
                url=url,
                headers={"Authorization": f"Bearer {token}"},
                params=params,
            )
            if response.status_code == 401:
                raise AuthenticationError("Invalid or expired token")
            if response.status_code == 403:
                raise AuthorizationError("Access denied by IAM")
            response.raise_for_status()
            if response.content:
                data = response.json()
                return data if isinstance(data, dict) else {"data": data}
            return {}
        except (AuthenticationError, AuthorizationError):
            raise
        except httpx.TimeoutException as exc:
            logger.error("iam_timeout", path=url)
            raise IAMServiceError(f"IAM request timed out: {url}", details={"path": url}) from exc
        except httpx.HTTPStatusError as exc:
            raise IAMServiceError(
                f"IAM returned HTTP {exc.response.status_code}",
                details={"path": url, "status_code": exc.response.status_code},
            ) from exc
        except httpx.RequestError as exc:
            raise IAMServiceError(f"IAM service unreachable: {exc}", details={"path": url}) from exc

    async def validate_token(self, token: str) -> TokenValidationResult:
        data = await self._request("POST", settings.iam_validate_token_path, token=token)
        return TokenValidationResult(
            valid=data.get("valid", True),
            user_id=str(data.get("userId") or data.get("user_id") or ""),
            expires_at=data.get("expiresAt") or data.get("expires_at"),
            roles=data.get("roles", []),
        )

    async def fetch_permissions(self, token: str) -> IAMUserProfile:
        data = await self._request("GET", settings.iam_permissions_path, token=token)
        return parse_iam_profile(data)

    async def fetch_module_access(self, token: str) -> list[ModuleAccess]:
        data = await self._request("GET", settings.iam_modules_path, token=token)
        modules_raw = data.get("modules") or data.get("data") or data
        if isinstance(modules_raw, dict):
            modules_raw = modules_raw.get("modules", [])
        return [
            ModuleAccess(
                module_id=str(m.get("moduleId") or m.get("module_id") or m.get("id", "")),
                module_name=m.get("moduleName") or m.get("module_name") or m.get("name"),
                permissions=m.get("permissions", []),
                enabled=m.get("enabled", True),
            )
            for m in modules_raw
            if isinstance(m, dict)
        ]

    async def fetch_allowed_actions(self, token: str, *, module_id: str | None = None) -> list[str]:
        params = {"moduleId": module_id} if module_id else None
        data = await self._request("GET", settings.iam_actions_path, token=token, params=params)
        actions = data.get("actions") or data.get("allowedActions") or data.get("allowed_actions") or []
        return list(actions)

    async def get_user_permissions(self, token: str) -> UserContext:
        """Backward-compatible alias for resolve_user_context."""
        return await self.resolve_user_context(token)

    async def resolve_user_context(self, token: str, *, use_cache: bool = True) -> UserContext:
        if use_cache:
            cached = await self._cache.get(token)
            if cached is not None:
                return cached

        await self.validate_token(token)
        profile = await self.fetch_permissions(token)

        if not profile.modules:
            try:
                profile.modules = await self.fetch_module_access(token)
            except IAMServiceError:
                logger.warning("iam_module_access_fallback")

        if not profile.allowed_actions:
            try:
                profile.allowed_actions = await self.fetch_allowed_actions(token)
            except IAMServiceError:
                logger.warning("iam_actions_fallback")

        user = UserContext.from_profile(profile)

        if use_cache:
            await self._cache.set(token, user)

        logger.info(
            "iam_context_resolved",
            user_id=user.user_id,
            permission_count=len(user.effective_permissions),
            module_count=len(user.modules),
        )
        return user

    async def invalidate_cache(self, token: str) -> None:
        await self._cache.invalidate(token)
