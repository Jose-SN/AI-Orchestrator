"""Application layer ports (interfaces) — hexagonal architecture boundaries."""

from typing import Any, Protocol

from langchain_core.language_models.chat_models import BaseChatModel

from app.domain.auth.models import UserContext


class LLMPort(Protocol):
    @property
    def provider_name(self) -> str: ...

    def get_chat_model(self) -> BaseChatModel: ...


class AgentPort(Protocol):
    @property
    def provider_name(self) -> str: ...

    async def run(
        self,
        *,
        message: str,
        user: UserContext,
        token: str,
        conversation_id: str,
        agent_id: str | None = None,
    ) -> dict[str, Any]: ...


class VectorStorePort(Protocol):
    async def search(self, query: str, *, limit: int = 5) -> list[dict[str, Any]]: ...

    async def upsert(self, documents: list[dict[str, Any]]) -> None: ...


class AuditPort(Protocol):
    def log_chat_request(self, *, user_id: str, conversation_id: str) -> None: ...

    def log_tool_invocation(
        self,
        *,
        user_id: str,
        tool_name: str,
        outcome: str,
    ) -> None: ...
