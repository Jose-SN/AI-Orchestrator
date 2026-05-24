"""Execution context injected into every tool call."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ToolExecutionContext:
    """Runtime context — never exposed to the LLM, injected by the registry wrapper."""

    token: str
    user_id: str
    trace_id: str | None = None
    request_id: str | None = None
    conversation_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
