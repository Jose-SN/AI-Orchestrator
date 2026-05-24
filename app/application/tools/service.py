"""Permission-aware tool registry service."""

from langchain_core.tools import StructuredTool

from app.core.logging import AuditAction, audit_log, get_logger
from app.domain.auth.models import UserContext
from app.domain.tools.models import ToolRegistrySnapshot
from app.infrastructure.tools.loader import PermissionAwareToolLoader
from app.infrastructure.tools.registry import ToolRegistry, tool_registry

logger = get_logger(__name__)


class ToolRegistryService:
    """
    Application service for dynamic, permission-filtered tool loading.

    The AI agent receives ONLY tools the user is authorized to use.
    """

    def __init__(
        self,
        registry: ToolRegistry | None = None,
        loader: PermissionAwareToolLoader | None = None,
    ) -> None:
        self._registry = registry or tool_registry
        self._loader = loader or PermissionAwareToolLoader(self._registry)

    def get_snapshot(self, user: UserContext) -> ToolRegistrySnapshot:
        snapshot = self._registry.snapshot(user.permissions)
        allowed_defs = self._registry.get_allowed_definitions(user.permissions)

        by_operation: dict[str, list[str]] = {}
        by_category: dict[str, list[str]] = {}
        for tool in allowed_defs:
            by_operation.setdefault(tool.operation.value, []).append(tool.name)
            by_category.setdefault(tool.category, []).append(tool.name)

        return snapshot.model_copy(
            update={"tools_by_operation": by_operation, "tools_by_category": by_category},
        )

    def load_langchain_tools(
        self,
        user: UserContext,
        *,
        token: str,
        trace_id: str | None = None,
        request_id: str | None = None,
        conversation_id: str | None = None,
    ) -> list[StructuredTool]:
        """Load permission-filtered LangChain tools for the agent."""
        tools = self._loader.load_for_user(
            user,
            token=token,
            trace_id=trace_id,
            request_id=request_id,
            conversation_id=conversation_id,
        )

        allowed_defs = self._registry.get_allowed_definitions(user.permissions)
        allowed_names = {d.name for d in allowed_defs}
        all_names = {d.name for d in self._registry.get_all_definitions()}
        denied_count = len(all_names - allowed_names)
        if denied_count:
            audit_log(
                AuditAction.PERMISSION_DENIED,
                user_id=user.user_id,
                conversation_id=conversation_id,
                metadata={"denied_tool_count": denied_count},
            )

        logger.info(
            "tools_loaded_for_agent",
            user_id=user.user_id,
            allowed_count=len(tools),
            trace_id=trace_id,
        )
        return tools
