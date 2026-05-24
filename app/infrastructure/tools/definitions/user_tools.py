"""User-related tools — call User microservice APIs."""

import json

from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.infrastructure.http.microservice_client import UserServiceClient
from app.infrastructure.tools.registry import register_tool

logger = get_logger(__name__)
_user_client = UserServiceClient()


class GetUserProfileInput(BaseModel):
    lookup_user_id: str | None = Field(
        default=None,
        description="User ID to look up. Defaults to the authenticated user.",
    )


@register_tool(
    name="get_user_profile",
    description=(
        "Retrieve a user's profile information including name, email, and roles. "
        "Use when the user asks about their account, profile, or personal details."
    ),
    required_permissions=["users:read"],
    service="user-service",
    category="users",
    args_schema=GetUserProfileInput,
)
async def get_user_profile(
    *,
    token: str,
    user_id: str,
    lookup_user_id: str | None = None,
) -> str:
    target_id = lookup_user_id or user_id
    logger.info("tool_get_user_profile", target_user_id=target_id)
    try:
        data = await _user_client.get(f"/api/v1/users/{target_id}", token=token)
        return json.dumps(data, default=str)
    except Exception as exc:
        logger.error("tool_get_user_profile_failed", error=str(exc))
        return f"Unable to retrieve user profile: {exc}"


class ListUsersInput(BaseModel):
    search: str | None = Field(default=None, description="Optional search term for filtering users")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum number of users to return")


@register_tool(
    name="list_users",
    description=(
        "List users in the system with optional search filtering. "
        "Use when the user asks to see, find, or search for users."
    ),
    required_permissions=["users:read", "users:list"],
    service="user-service",
    category="users",
    args_schema=ListUsersInput,
)
async def list_users(
    *,
    token: str,
    user_id: str,  # noqa: ARG001 — auth context injection
    search: str | None = None,
    limit: int = 10,
) -> str:
    logger.info("tool_list_users", search=search, limit=limit)
    try:
        params: dict[str, str | int] = {"limit": limit}
        if search:
            params["search"] = search
        data = await _user_client.get("/api/v1/users", token=token, params=params)
        return json.dumps(data, default=str)
    except Exception as exc:
        logger.error("tool_list_users_failed", error=str(exc))
        return f"Unable to list users: {exc}"
