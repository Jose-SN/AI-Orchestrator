"""Tool metadata domain models."""

from collections.abc import Awaitable, Callable
from typing import Any

from pydantic import BaseModel, Field


class ToolDefinition(BaseModel):
    """Metadata for a registered orchestrator tool."""

    name: str
    description: str
    required_permissions: list[str] = Field(default_factory=list)
    service: str = Field(description="Downstream microservice this tool calls")
    category: str = "general"
    enabled: bool = True
    args_schema: type[BaseModel] | None = Field(default=None, exclude=True)
    handler: Callable[..., Awaitable[str]] | None = Field(default=None, exclude=True)

    model_config = {"arbitrary_types_allowed": True}

    def is_allowed_for_permissions(self, user_permissions: list[str]) -> bool:
        """Return True if the user has all required permissions for this tool."""
        if not self.required_permissions:
            return True
        return set(self.required_permissions).issubset(set(user_permissions))


class ToolRegistrySnapshot(BaseModel):
    """Snapshot of tools available for a given user session."""

    total_registered: int
    allowed_count: int
    allowed_tools: list[str]
    denied_tools: list[str] = Field(default_factory=list)
