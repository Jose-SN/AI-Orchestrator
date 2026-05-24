"""Permission resolution — delegates to IAM."""

from app.application.tools.service import ToolRegistryService
from app.core.logging import get_logger
from app.domain.auth.models import UserContext
from app.domain.tools.models import ToolRegistrySnapshot
from app.infrastructure.http.clients.iam import IAMClient

logger = get_logger(__name__)


class PermissionService:
    def __init__(
        self,
        iam_client: IAMClient,
        tool_registry_service: ToolRegistryService | None = None,
    ) -> None:
        self._iam = iam_client
        self._tools = tool_registry_service or ToolRegistryService()

    async def resolve_user_context(self, token: str) -> UserContext:
        user = await self._iam.get_user_permissions(token)
        logger.info("permissions_resolved", user_id=user.user_id, permission_count=len(user.permissions))
        return user

    def get_tool_snapshot(self, user: UserContext) -> ToolRegistrySnapshot:
        return self._tools.get_snapshot(user)
