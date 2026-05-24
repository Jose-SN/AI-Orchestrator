"""Structured agent execution results."""

from typing import Any

from pydantic import BaseModel, Field


class ToolCallRecord(BaseModel):
    tool_name: str
    input: dict[str, Any] = Field(default_factory=dict)
    output: str | None = None
    success: bool = True
    error: str | None = None


class AgentResult(BaseModel):
    """Parsed, structured output from a tool-calling agent run."""

    response: str
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)
    conversation_id: str
    provider: str
    model: str
    iterations: int = 0
    used_tools: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "response": self.response,
            "tool_invocations": [t.model_dump() for t in self.tool_calls],
            "conversation_id": self.conversation_id,
            "provider": self.provider,
            "model": self.model,
            "iterations": self.iterations,
            "used_tools": self.used_tools,
            "metadata": self.metadata,
        }
