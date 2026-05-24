"""Permission resolution — delegates to IAM, drives dynamic tool loading."""

from langchain_core.tools import StructuredTool

from app.application.tools.service import ToolRegistryService
from app.core.logging import AuditAction, audit_log, get_logger
from app.domain.auth.models import UserContext
from app.domain.tools.models import ToolRegistrySnapshot
from app.infrastructure.iam.client import IAMClient
from app.infrastructure.tools.registry import tool_registry

logger = get_logger(__name__)


class PermissionService:
    """
    Resolves IAM permissions and determines which tools are available per request.

    The orchestrator NEVER decides permissions — IAM is the sole authority.
    Tool availability is computed dynamically from effective_permissions.
    """

    def __init__(
        self,
        iam_client: IAMClient,
        tool_registry_service: ToolRegistryService | None = None,
    ) -> None:
        self._iam = iam_client
        self._tools = tool_registry_service or ToolRegistryService()

    async def resolve_user_context(self, token: str, *, use_cache: bool = True) -> UserContext:
        user = await self._iam.resolve_user_context(token, use_cache=use_cache)
        logger.info(
            "permissions_resolved",
            user_id=user.user_id,
            permission_count=len(user.effective_permissions),
            modules=len(user.modules),
            actions=len(user.allowed_actions),
        )
        return user

    async def invalidate_user_cache(self, token: str) -> None:
        await self._iam.invalidate_cache(token)

    def get_tool_snapshot(self, user: UserContext) -> ToolRegistrySnapshot:
        return self._tools.get_snapshot(user.effective_permissions)

    def get_allowed_tools(self, user: UserContext) -> list[str]:
        return [
            t.name
            for t in tool_registry.get_allowed_definitions(user.effective_permissions)
        ]

    async def load_agent_tools(
        self,
        user: UserContext,
        *,
        token: str,
        trace_id: str | None = None,
        conversation_id: str | None = None,
    ) -> list[StructuredTool]:
        """Load LangChain tools dynamically filtered by IAM permissions."""
        tools = self._tools.load_langchain_tools(
            user.model_copy(update={"permissions": user.effective_permissions}),
            token=token,
            trace_id=trace_id,
            conversation_id=conversation_id,
        )

        audit_log(
            AuditAction.AGENT_EXECUTION,
            user_id=user.user_id,
            conversation_id=conversation_id,
            metadata={
                "allowed_tools": [t.name for t in tools],
                "trace_id": trace_id,
            },
        )
        return tools

    def has_module_access(self, user: UserContext, module_id: str) -> bool:
        return user.has_module_access(module_id)

    def has_action(self, user: UserContext, action: str) -> bool:
        return user.has_action(action)
