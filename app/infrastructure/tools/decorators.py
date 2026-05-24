"""LangChain-compatible orchestrator tool decorator."""

from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any

from pydantic import BaseModel

from app.domain.tools.context import ToolExecutionContext
from app.domain.tools.models import ToolOperation
from app.infrastructure.tools.base.executor import execute_with_hooks
from app.infrastructure.tools.registry import tool_registry


def orchestrator_tool(
    *,
    name: str,
    description: str,
    required_permissions: list[str],
    service: str,
    operation: ToolOperation,
    category: str = "general",
    args_schema: type[BaseModel] | None = None,
) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]:
    """
    Register a modular tool with IAM permissions, tracing, audit, and structured responses.

    Handler signature: async def handler(ctx: ToolExecutionContext, **llm_params) -> ToolResponse | dict
    Auth context (token, trace_id) is injected — never visible to the LLM.
    """

    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @wraps(func)
        async def instrumented(ctx: ToolExecutionContext, **kwargs: Any) -> str:
            return await execute_with_hooks(
                tool_name=name,
                operation=operation,
                ctx=ctx,
                handler=func,
                **kwargs,
            )

        async def registry_handler(*, token: str, user_id: str, **kwargs: Any) -> str:
            ctx = ToolExecutionContext(
                token=token,
                user_id=user_id,
                trace_id=kwargs.pop("_trace_id", None),
                request_id=kwargs.pop("_request_id", None),
                conversation_id=kwargs.pop("_conversation_id", None),
            )
            return await instrumented(ctx, **kwargs)

        tool_registry.register(
            name=name,
            description=description,
            handler=registry_handler,
            required_permissions=required_permissions,
            service=service,
            category=category,
            operation=operation,
            args_schema=args_schema,
        )
        return func

    return decorator


register_tool = orchestrator_tool
