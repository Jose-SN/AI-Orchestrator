"""Multi-agent registry — routes requests to specialized agents."""

from app.application.permissions.service import PermissionService
from app.application.tools.service import ToolRegistryService
from app.core.config import settings
from app.core.logging import get_logger
from app.domain.agents.models import AgentDefinition, AgentType
from app.infrastructure.agents.langgraph.orchestrator import LangGraphOrchestratorAgent

logger = get_logger(__name__)


class AgentRegistry:
    def __init__(
        self,
        tool_registry_service: ToolRegistryService | None = None,
        permission_service: PermissionService | None = None,
    ) -> None:
        self._definitions: dict[str, AgentDefinition] = {}
        self._tool_service = tool_registry_service or ToolRegistryService()
        self._permission_service = permission_service
        self._default_orchestrator = LangGraphOrchestratorAgent(
            self._tool_service, permission_service
        )
        self._register_defaults()

    def _register_defaults(self) -> None:
        self.register(
            AgentDefinition(
                id="orchestrator",
                name="Main Orchestrator",
                description="Default conversational agent with permission-filtered tools",
                agent_type=AgentType.ORCHESTRATOR,
            )
        )

    def register(self, definition: AgentDefinition) -> None:
        self._definitions[definition.id] = definition
        logger.debug("agent_registered", agent_id=definition.id)

    def get_definition(self, agent_id: str) -> AgentDefinition | None:
        return self._definitions.get(agent_id)

    def resolve(self, agent_id: str | None = None) -> LangGraphOrchestratorAgent:
        """Resolve agent runtime. Extend for supervisor/multi-agent routing."""
        target_id = agent_id or settings.default_agent_id
        if target_id not in self._definitions:
            logger.warning("agent_not_found", agent_id=target_id)
        return self._default_orchestrator

    async def run(
        self,
        *,
        message: str,
        user,
        token: str,
        conversation_id: str,
        agent_id: str | None = None,
    ) -> dict:
        """AgentPort implementation — delegates to resolved agent."""
        agent = self.resolve(agent_id)
        result = await agent.run(
            message=message,
            user=user,
            token=token,
            conversation_id=conversation_id,
        )
        result["agent_id"] = agent_id or settings.default_agent_id
        return result

    def list_agents(self) -> list[AgentDefinition]:
        return list(self._definitions.values())
