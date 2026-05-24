"""Permission-aware dynamic tool loader."""

from langchain_core.tools import StructuredTool

from app.core.logging import get_logger
from app.domain.auth.models import UserContext
from app.infrastructure.tools.registry import ToolRegistry, tool_registry

logger = get_logger(__name__)


class PermissionAwareToolLoader:
    """Loads tools dynamically based on IAM permissions."""

    def __init__(self, registry: ToolRegistry | None = None) -> None:
        self._registry = registry or tool_registry

    def load_for_user(
        self,
        user: UserContext,
        *,
        token: str,
        trace_id: str | None = None,
        request_id: str | None = None,
        conversation_id: str | None = None,
        category: str | None = None,
    ) -> list[StructuredTool]:
        if category:
            definitions = self._registry.get_by_category(category, user.permissions)
            all_tools = self._registry.to_langchain_tools(
                user, token=token, trace_id=trace_id,
                request_id=request_id, conversation_id=conversation_id,
            )
            allowed_names = {d.name for d in definitions}
            return [t for t in all_tools if t.name in allowed_names]

        return self._registry.to_langchain_tools(
            user,
            token=token,
            trace_id=trace_id,
            request_id=request_id,
            conversation_id=conversation_id,
        )

    def get_allowed_tool_names(self, user: UserContext) -> list[str]:
        return [t.name for t in self._registry.get_allowed_definitions(user.permissions)]


def load_all_tools() -> None:
    """Import all tool modules to trigger @orchestrator_tool registration."""
    from app.infrastructure.tools.definitions import (  # noqa: F401
        customer_tools,
        module_tools,
        user_tools,
    )
    logger.info("all_tools_loaded")
