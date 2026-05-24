"""Dependency injection container — single composition root."""

from dataclasses import dataclass, field

from app.application.agents.registry import AgentRegistry
from app.application.chat.service import ChatService
from app.application.permissions.service import PermissionService
from app.core.config import Settings, get_settings
from app.infrastructure.http.clients.iam import IAMClient
from app.infrastructure.http.clients.microservices import MicroserviceClientFactory
from app.infrastructure.vector.factory import create_vector_store


@dataclass
class AppContainer:
    """
    Explicit DI container. All dependencies are wired here for testability.

    In tests, create AppContainer with overridden settings or mock clients.
    """

    settings: Settings = field(default_factory=get_settings)
    _iam_client: IAMClient | None = field(default=None, init=False, repr=False)
    _microservices: MicroserviceClientFactory | None = field(default=None, init=False, repr=False)
    _agent_registry: AgentRegistry | None = field(default=None, init=False, repr=False)
    _permission_service: PermissionService | None = field(default=None, init=False, repr=False)
    _chat_service: ChatService | None = field(default=None, init=False, repr=False)

    def iam_client(self) -> IAMClient:
        if self._iam_client is None:
            self._iam_client = IAMClient()
        return self._iam_client

    def microservice_factory(self) -> MicroserviceClientFactory:
        if self._microservices is None:
            self._microservices = MicroserviceClientFactory()
        return self._microservices

    def agent_registry(self) -> AgentRegistry:
        if self._agent_registry is None:
            self._agent_registry = AgentRegistry()
        return self._agent_registry

    def permission_service(self) -> PermissionService:
        if self._permission_service is None:
            self._permission_service = PermissionService(self.iam_client())
        return self._permission_service

    def chat_service(self) -> ChatService:
        if self._chat_service is None:
            self._chat_service = ChatService(
                permission_service=self.permission_service(),
                agent=self.agent_registry(),
            )
        return self._chat_service

    def vector_store(self):
        return create_vector_store(self.settings)

    async def shutdown(self) -> None:
        if self._iam_client:
            await self._iam_client.close()
        if self._microservices:
            await self._microservices.close_all()


_container: AppContainer | None = None


def get_container() -> AppContainer:
    global _container
    if _container is None:
        _container = AppContainer()
    return _container


def reset_container() -> None:
    """Reset container — use in tests."""
    global _container
    _container = None
