"""Chat bounded context — domain models."""

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
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000)
    conversation_id: str | None = None
    agent_id: str | None = Field(default=None, description="Target agent for multi-agent routing")
    context: dict[str, Any] = Field(default_factory=dict)


class ToolInvocation(BaseModel):
    tool_name: str
    input: dict[str, Any] = Field(default_factory=dict)
    output: str | None = None
    success: bool = True


class ChatResponse(BaseModel):
    conversation_id: str
    message: str
    tools_used: list[ToolInvocation] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class StreamChatChunk(BaseModel):
    conversation_id: str
    delta: str
    is_final: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


def new_conversation_id() -> str:
    return str(uuid4())
