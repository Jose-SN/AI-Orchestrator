"""User tools — refactored to use orchestrator_tool decorator."""

from pydantic import BaseModel, Field

from app.domain.tools.context import ToolExecutionContext
from app.domain.tools.models import ToolOperation
from app.infrastructure.http.clients.microservices import UserServiceClient
from app.infrastructure.tools.base.api_tool import BaseAPITool
from app.infrastructure.tools.decorators import orchestrator_tool

_user_api = BaseAPITool(UserServiceClient())
_user_api.service_name = "user-service"
_user_api.resource_path = "/api/v1/users"


class GetUserProfileInput(BaseModel):
    lookup_user_id: str | None = Field(default=None, description="User ID to look up. Defaults to authenticated user.")


class ListUsersInput(BaseModel):
    search: str | None = Field(default=None, description="Optional search term")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum users to return")


@orchestrator_tool(
    name="get_user_profile",
    description="Retrieve a user's profile including name, email, and roles.",
    required_permissions=["users:read"],
    service="user-service",
    operation=ToolOperation.GET,
    category="users",
    args_schema=GetUserProfileInput,
)
async def get_user_profile(ctx: ToolExecutionContext, lookup_user_id: str | None = None):
    target_id = lookup_user_id or ctx.user_id
    return await _user_api.get(ctx, target_id, tool_name="get_user_profile")


@orchestrator_tool(
    name="list_users",
    description="List users with optional search filtering.",
    required_permissions=["users:read", "users:list"],
    service="user-service",
    operation=ToolOperation.LIST,
    category="users",
    args_schema=ListUsersInput,
)
async def list_users(ctx: ToolExecutionContext, search: str | None = None, limit: int = 10):
    params: dict = {"limit": limit}
    if search:
        params["search"] = search
    return await _user_api.list(ctx, tool_name="list_users", params=params)
