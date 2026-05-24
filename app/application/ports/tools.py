"""Tool registry port — application boundary."""

from typing import Protocol

from langchain_core.tools import StructuredTool

from app.domain.auth.models import UserContext
from app.domain.tools.models import ToolDefinition, ToolRegistrySnapshot


class ToolRegistryPort(Protocol):
    def get_all_definitions(self) -> list[ToolDefinition]: ...

    def get_allowed_definitions(self, user_permissions: list[str]) -> list[ToolDefinition]: ...

    def snapshot(self, user_permissions: list[str]) -> ToolRegistrySnapshot: ...

    def to_langchain_tools(
        self,
        user: UserContext,
        *,
        token: str,
        trace_id: str | None = None,
        request_id: str | None = None,
        conversation_id: str | None = None,
    ) -> list[StructuredTool]: ...
