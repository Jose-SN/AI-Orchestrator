"""Downstream microservice HTTP clients."""

from app.core.config import settings
from app.infrastructure.http.clients.base import BaseHTTPClient


class UserServiceClient(BaseHTTPClient):
    def __init__(self) -> None:
        super().__init__(base_url=settings.user_service_url, service_name="user-service")


class ModuleServiceClient(BaseHTTPClient):
    def __init__(self) -> None:
        super().__init__(base_url=settings.module_service_url, service_name="module-service")


class CustomerServiceClient(BaseHTTPClient):
    def __init__(self) -> None:
        super().__init__(base_url=settings.customer_service_url, service_name="customer-service")


class MicroserviceClientFactory:
    def __init__(self) -> None:
        self._user_client = UserServiceClient()
        self._module_client = ModuleServiceClient()
        self._customer_client = CustomerServiceClient()

    @property
    def user_service(self) -> UserServiceClient:
        return self._user_client

    @property
    def module_service(self) -> ModuleServiceClient:
        return self._module_client

    @property
    def customer_service(self) -> CustomerServiceClient:
        return self._customer_client

    async def close_all(self) -> None:
        await self._user_client.close()
        await self._module_client.close()
        await self._customer_client.close()
