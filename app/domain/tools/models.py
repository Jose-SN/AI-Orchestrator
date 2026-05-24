"""Tool domain models."""

from collections.abc import Awaitable, Callable
from enum import Enum

from pydantic import BaseModel, Field


class ToolOperation(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    SEARCH = "search"
    LIST = "list"
    GET = "get"


class ToolDefinition(BaseModel):
    name: str
    description: str
    required_permissions: list[str] = Field(default_factory=list)
    service: str
    category: str = "general"
    operation: ToolOperation = ToolOperation.GET
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
    tools_by_operation: dict[str, list[str]] = Field(default_factory=dict)
    tools_by_category: dict[str, list[str]] = Field(default_factory=dict)
