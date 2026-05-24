"""Structured tool response contract returned to the LLM."""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from app.domain.tools.models import ToolOperation


class ToolResponse(BaseModel):
    """Uniform JSON-serializable response from every tool."""

    success: bool
    tool_name: str
    operation: ToolOperation
    data: Any | None = None
    error: str | None = None
    error_code: str | None = None
    trace_id: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def to_json(self) -> str:
        return self.model_dump_json(exclude_none=True)

    @classmethod
    def ok(
        cls,
        *,
        tool_name: str,
        operation: ToolOperation,
        data: Any,
        trace_id: str | None = None,
    ) -> "ToolResponse":
        return cls(
            success=True,
            tool_name=tool_name,
            operation=operation,
            data=data,
            trace_id=trace_id,
        )

    @classmethod
    def fail(
        cls,
        *,
        tool_name: str,
        operation: ToolOperation,
        error: str,
        error_code: str = "TOOL_ERROR",
        trace_id: str | None = None,
    ) -> "ToolResponse":
        return cls(
            success=False,
            tool_name=tool_name,
            operation=operation,
            error=error,
            error_code=error_code,
            trace_id=trace_id,
        )
