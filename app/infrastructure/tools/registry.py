"""Modular tool registration and permission-aware loading."""

from collections.abc import Awaitable, Callable
from typing import Any

from langchain_core.tools import StructuredTool
from pydantic import BaseModel

from app.core.logging import get_logger
from app.domain.auth.models import UserContext
from app.domain.tools.context import ToolExecutionContext
from app.domain.tools.models import ToolDefinition, ToolOperation, ToolRegistrySnapshot

logger = get_logger(__name__)


class ToolRegistry:
    """Central registry — tools declare IAM permissions; only allowed tools reach the agent."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(
        self,
        *,
        name: str,
        description: str,
        handler: Callable[..., Awaitable[str]],
        required_permissions: list[str] | None = None,
        service: str = "unknown",
        category: str = "general",
        operation: ToolOperation = ToolOperation.GET,
        args_schema: type[BaseModel] | None = None,
    ) -> None:
        if name in self._tools:
            logger.warning("tool_reregistered", tool_name=name)

        self._tools[name] = ToolDefinition(
            name=name,
            description=description,
            required_permissions=required_permissions or [],
            service=service,
            category=category,
            operation=operation,
            handler=handler,
            args_schema=args_schema,
        )
        logger.debug("tool_registered", tool_name=name, operation=operation.value, service=service)

    def get_all_definitions(self) -> list[ToolDefinition]:
        return list(self._tools.values())

    def get_allowed_definitions(self, user_permissions: list[str]) -> list[ToolDefinition]:
        return [
            t for t in self._tools.values()
            if t.enabled and t.is_allowed_for_permissions(user_permissions)
        ]

    def get_by_category(self, category: str, user_permissions: list[str]) -> list[ToolDefinition]:
        return [t for t in self.get_allowed_definitions(user_permissions) if t.category == category]

    def get_by_operation(self, operation: ToolOperation, user_permissions: list[str]) -> list[ToolDefinition]:
        return [t for t in self.get_allowed_definitions(user_permissions) if t.operation == operation]

    def snapshot(self, user_permissions: list[str]) -> ToolRegistrySnapshot:
        allowed = [t.name for t in self.get_allowed_definitions(user_permissions)]
        allowed_set = set(allowed)
        denied = [name for name in self._tools if name not in allowed_set]
        return ToolRegistrySnapshot(
            total_registered=len(self._tools),
            allowed_count=len(allowed),
            allowed_tools=allowed,
            denied_tools=denied,
        )

    def to_langchain_tools(
        self,
        user: UserContext,
        *,
        token: str,
        trace_id: str | None = None,
        request_id: str | None = None,
        conversation_id: str | None = None,
    ) -> list[StructuredTool]:
        langchain_tools: list[StructuredTool] = []

        for tool_def in self.get_allowed_definitions(user.permissions):
            if tool_def.handler is None:
                continue

            handler = self._wrap_handler(
                tool_def.handler,
                token=token,
                user_id=user.user_id,
                trace_id=trace_id,
                request_id=request_id,
                conversation_id=conversation_id,
            )

            lc_tool = StructuredTool.from_function(
                coroutine=handler,
                name=tool_def.name,
                description=tool_def.description,
                args_schema=tool_def.args_schema,
            )
            langchain_tools.append(lc_tool)

        logger.info(
            "langchain_tools_built",
            user_id=user.user_id,
            count=len(langchain_tools),
            tools=[t.name for t in langchain_tools],
            trace_id=trace_id,
        )
        return langchain_tools

    @staticmethod
    def _wrap_handler(
        handler: Callable[..., Awaitable[str]],
        *,
        token: str,
        user_id: str,
        trace_id: str | None,
        request_id: str | None,
        conversation_id: str | None,
    ) -> Callable[..., Awaitable[str]]:
        async def wrapped(**kwargs: Any) -> str:
            return await handler(
                token=token,
                user_id=user_id,
                _trace_id=trace_id,
                _request_id=request_id,
                _conversation_id=conversation_id,
                **kwargs,
            )

        return wrapped


tool_registry = ToolRegistry()
