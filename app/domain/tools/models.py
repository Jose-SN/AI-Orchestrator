"""Tool bounded context — tool metadata models."""

from collections.abc import Awaitable, Callable
from typing import Any

from pydantic import BaseModel, Field


class ToolDefinition(BaseModel):
    name: str
    description: str
    required_permissions: list[str] = Field(default_factory=list)
    service: str
    category: str = "general"
    enabled: bool = True
    args_schema: type[BaseModel] | None = Field(default=None, exclude=True)
    handler: Callable[..., Awaitable[str]] | None = Field(default=None, exclude=True)

    model_config = {"arbitrary_types_allowed": True}

    def is_allowed_for_permissions(self, user_permissions: list[str]) -> bool:
        if not self.required_permissions:
            return True
        return set(self.required_permissions).issubset(set(user_permissions))


class ToolRegistrySnapshot(BaseModel):
    total_registered: int
    allowed_count: int
    allowed_tools: list[str]
    denied_tools: list[str] = Field(default_factory=list)
