"""Tool execution wrapper — tracing, audit, structured errors."""

from typing import Any

import structlog
from collections.abc import Awaitable, Callable

from app.core.exceptions import DownstreamServiceError
from app.core.logging import AuditAction, audit_log, get_logger
from app.core.observability.context import get_trace_id
from app.core.observability.metrics import increment_counter
from app.domain.tools.context import ToolExecutionContext
from app.domain.tools.models import ToolOperation
from app.domain.tools.response import ToolResponse

logger = get_logger(__name__)


async def execute_with_hooks(
    *,
    tool_name: str,
    operation: ToolOperation,
    ctx: ToolExecutionContext,
    handler: Callable[..., Awaitable[Any]],
    **kwargs: Any,
) -> str:
    """
    Execute a tool handler with tracing, audit logging, metrics, and structured responses.

    Returns JSON string for LangChain consumption.
    """
    trace_id = ctx.trace_id or get_trace_id()
    structlog.contextvars.bind_contextvars(
        tool_name=tool_name,
        trace_id=trace_id,
        user_id=ctx.user_id,
    )

    increment_counter("tool_invocations_total", tool=tool_name, operation=operation.value)
    logger.info("tool_execution_started", tool_name=tool_name, operation=operation.value, trace_id=trace_id)

    audit_log(
        AuditAction.TOOL_INVOKED,
        user_id=ctx.user_id,
        conversation_id=ctx.conversation_id,
        resource=tool_name,
        outcome="started",
        metadata={"operation": operation.value, "trace_id": trace_id},
    )

    try:
        result = await handler(ctx=ctx, **kwargs)

        if isinstance(result, ToolResponse):
            response = result
        elif isinstance(result, str):
            return result
        else:
            response = ToolResponse.ok(
                tool_name=tool_name,
                operation=operation,
                data=result,
                trace_id=trace_id,
            )

        audit_log(
            AuditAction.TOOL_INVOKED,
            user_id=ctx.user_id,
            conversation_id=ctx.conversation_id,
            resource=tool_name,
            outcome="success",
            metadata={"operation": operation.value, "trace_id": trace_id},
        )
        logger.info("tool_execution_completed", tool_name=tool_name, trace_id=trace_id)
        return response.to_json()

    except DownstreamServiceError as exc:
        response = ToolResponse.fail(
            tool_name=tool_name,
            operation=operation,
            error=f"Service '{exc.service}' unavailable",
            error_code="DOWNSTREAM_ERROR",
            trace_id=trace_id,
        )
        audit_log(
            AuditAction.TOOL_INVOKED,
            user_id=ctx.user_id,
            conversation_id=ctx.conversation_id,
            resource=tool_name,
            outcome="failure",
            metadata={"error_code": "DOWNSTREAM_ERROR", "trace_id": trace_id},
        )
        logger.warning("tool_downstream_error", tool_name=tool_name, service=exc.service, trace_id=trace_id)
        return response.to_json()

    except Exception as exc:
        response = ToolResponse.fail(
            tool_name=tool_name,
            operation=operation,
            error="An unexpected error occurred while executing the tool",
            error_code="INTERNAL_ERROR",
            trace_id=trace_id,
        )
        audit_log(
            AuditAction.TOOL_INVOKED,
            user_id=ctx.user_id,
            conversation_id=ctx.conversation_id,
            resource=tool_name,
            outcome="failure",
            metadata={"error_code": "INTERNAL_ERROR", "trace_id": trace_id},
        )
        logger.exception("tool_execution_failed", tool_name=tool_name, trace_id=trace_id, error=str(exc))
        return response.to_json()
