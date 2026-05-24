"""Modular tool registration and permission-aware loading."""

from collections.abc import Awaitable, Callable
from typing import Any

from langchain_core.tools import StructuredTool
from pydantic import BaseModel

from app.core.logging import get_logger
from app.domain.models.tool import ToolDefinition, ToolRegistrySnapshot

logger = get_logger(__name__)


class ToolRegistry:
    """
    Central registry for orchestrator tools.

    Tools declare required IAM permissions. Only tools whose permission
    requirements are satisfied by the user are loaded into the agent.
    """

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
        args_schema: type[BaseModel] | None = None,
    ) -> None:
        """Register a tool with metadata and async handler."""
        if name in self._tools:
            logger.warning("tool_reregistered", tool_name=name)

        self._tools[name] = ToolDefinition(
            name=name,
            description=description,
            required_permissions=required_permissions or [],
            service=service,
            category=category,
            handler=handler,
            args_schema=args_schema,
        )

        logger.debug(
            "tool_registered",
            tool_name=name,
            permissions=required_permissions,
            service=service,
        )

    def get_all_definitions(self) -> list[ToolDefinition]:
        return list(self._tools.values())

    def get_allowed_definitions(self, user_permissions: list[str]) -> list[ToolDefinition]:
        return [
            tool
            for tool in self._tools.values()
            if tool.enabled and tool.is_allowed_for_permissions(user_permissions)
        ]

    def snapshot(self, user_permissions: list[str]) -> ToolRegistrySnapshot:
        allowed = [t.name for t in self.get_allowed_definitions(user_permissions)]
        denied = [t.name for t in self._tools.values() if t.name not in allowed]
        return ToolRegistrySnapshot(
            total_registered=len(self._tools),
            allowed_count=len(allowed),
            allowed_tools=allowed,
            denied_tools=denied,
        )

    def to_langchain_tools(
        self,
        user_permissions: list[str],
        *,
        token: str,
        user_id: str,
    ) -> list[StructuredTool]:
        """Convert permission-filtered tools into LangChain StructuredTool instances."""
        langchain_tools: list[StructuredTool] = []

        for tool_def in self.get_allowed_definitions(user_permissions):
            if tool_def.handler is None:
                continue

            handler = self._wrap_handler(tool_def.handler, token=token, user_id=user_id)

            lc_tool = StructuredTool.from_function(
                coroutine=handler,
                name=tool_def.name,
                description=tool_def.description,
                args_schema=tool_def.args_schema,
            )
            langchain_tools.append(lc_tool)

        logger.info(
            "langchain_tools_loaded",
            count=len(langchain_tools),
            tools=[t.name for t in langchain_tools],
        )
        return langchain_tools

    @staticmethod
    def _wrap_handler(
        handler: Callable[..., Awaitable[str]],
        *,
        token: str,
        user_id: str,
    ) -> Callable[..., Awaitable[str]]:
        """Inject auth context into tool handlers without exposing token to the LLM."""

        async def wrapped(**kwargs: Any) -> str:
            return await handler(token=token, user_id=user_id, **kwargs)

        return wrapped


# Global singleton — populated at startup via tool modules
tool_registry = ToolRegistry()


def register_tool(
    *,
    name: str,
    description: str,
    required_permissions: list[str] | None = None,
    service: str = "unknown",
    category: str = "general",
    args_schema: type[BaseModel] | None = None,
) -> Callable[[Callable[..., Awaitable[str]]], Callable[..., Awaitable[str]]]:
    """Decorator for registering async tool handlers."""

    def decorator(func: Callable[..., Awaitable[str]]) -> Callable[..., Awaitable[str]]:
        tool_registry.register(
            name=name,
            description=description,
            handler=func,
            required_permissions=required_permissions,
            service=service,
            category=category,
            args_schema=args_schema,
        )
        return func

    return decorator
