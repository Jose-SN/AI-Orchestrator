"""Chat domain models."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class ChatMessage(BaseModel):
    """A single message in a conversation."""

    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChatRequest(BaseModel):
    """Incoming chat request from a client."""

    message: str = Field(..., min_length=1, max_length=8000)
    conversation_id: str | None = Field(
        default=None,
        description="Optional conversation ID for multi-turn context",
    )
    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional client-provided context (locale, tenant hints, etc.)",
    )


class ToolInvocation(BaseModel):
    """Record of a tool invoked during agent execution."""

    tool_name: str
    input: dict[str, Any] = Field(default_factory=dict)
    output: str | None = None
    success: bool = True


class ChatResponse(BaseModel):
    """Structured chat response returned to clients."""

    conversation_id: str
    message: str
    tools_used: list[ToolInvocation] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class StreamChatChunk(BaseModel):
    """Single chunk for future streaming responses."""

    conversation_id: str
    delta: str
    is_final: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


def new_conversation_id() -> str:
    """Generate a new conversation identifier."""
    return str(uuid4())
