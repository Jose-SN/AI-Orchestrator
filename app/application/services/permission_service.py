"""Permission resolution service — delegates to IAM, never decides permissions locally."""

from app.core.logging import get_logger
from app.domain.models.permission import UserContext
from app.domain.models.tool import ToolRegistrySnapshot
from app.infrastructure.http.iam_client import IAMClient
from app.infrastructure.tools.registry import tool_registry

logger = get_logger(__name__)


class PermissionService:
    """Resolves user permissions via IAM and filters available tools."""

    def __init__(self, iam_client: IAMClient) -> None:
        self._iam = iam_client

    async def resolve_user_context(self, token: str) -> UserContext:
        """Fetch authenticated user context and permissions from IAM."""
        user = await self._iam.get_user_permissions(token)
        logger.info(
            "permissions_resolved",
            user_id=user.user_id,
            permission_count=len(user.permissions),
        )
        return user

    def get_tool_snapshot(self, user: UserContext) -> ToolRegistrySnapshot:
        """Return which tools are available for this user."""
        return tool_registry.snapshot(user.permissions)
