"""Generic microservice HTTP client factory."""

from app.core.config import settings
from app.infrastructure.http.base_client import BaseHTTPClient


class UserServiceClient(BaseHTTPClient):
    """HTTP client for the User microservice."""

    def __init__(self) -> None:
        super().__init__(
            base_url=settings.user_service_url,
            service_name="user-service",
        )


class ModuleServiceClient(BaseHTTPClient):
    """HTTP client for the Module microservice."""

    def __init__(self) -> None:
        super().__init__(
            base_url=settings.module_service_url,
            service_name="module-service",
        )


class MicroserviceClientFactory:
    """Factory for creating typed downstream service clients."""

    def __init__(self) -> None:
        self._user_client = UserServiceClient()
        self._module_client = ModuleServiceClient()

    @property
    def user_service(self) -> UserServiceClient:
        return self._user_client

    @property
    def module_service(self) -> ModuleServiceClient:
        return self._module_client

    async def close_all(self) -> None:
        await self._user_client.close()
        await self._module_client.close()
