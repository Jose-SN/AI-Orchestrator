"""LangChain tool-calling agent — deterministic, API-only orchestration."""

from typing import Any

from langchain_core.tools import StructuredTool

from app.application.permissions.service import PermissionService
from app.application.tools.service import ToolRegistryService
from app.core.exceptions import AgentExecutionError
from app.core.logging import get_logger
from app.core.observability.context import get_trace_id
from app.domain.agents.config import AgentConfig
from app.domain.agents.result import AgentResult
from app.domain.auth.models import UserContext
from app.infrastructure.agents.config import load_agent_config
from app.infrastructure.agents.factory import ToolCallingAgentFactory

logger = get_logger(__name__)

NO_TOOLS_RESPONSE = (
    "I don't have any tools available for your account permissions. "
    "Please contact your administrator if you believe this is an error."
)


class ToolCallingAgent:
    """
    Tool-calling-only agent — no SQL, no autonomy, no direct DB access.

    Flow:
      1. Receive user message + IAM-filtered tools
      2. Build deterministic prompt
      3. LangGraph ReAct loop (tool calls only)
      4. Parse structured output
      5. Return formatted response
    """

    def __init__(
        self,
        factory: ToolCallingAgentFactory | None = None,
        tool_registry_service: ToolRegistryService | None = None,
        permission_service: PermissionService | None = None,
        config: AgentConfig | None = None,
    ) -> None:
        self._config = config or load_agent_config()
        self._factory = factory or ToolCallingAgentFactory(self._config)
        self._tool_service = tool_registry_service or ToolRegistryService()
        self._permission_service = permission_service

    @property
    def provider_name(self) -> str:
        return self._config.provider

    async def run(
        self,
        *,
        message: str,
        user: UserContext,
        token: str,
        conversation_id: str,
    ) -> dict[str, Any]:
        tools = await self._load_tools(user, token, conversation_id)
        if not tools:
            return AgentResult(
                response=NO_TOOLS_RESPONSE,
                conversation_id=conversation_id,
                provider=self.provider_name,
                model=self._config.model_name,
            ).to_dict()

        try:
            result = await self._execute(message, user, tools, conversation_id)
            return result.to_dict()
        except Exception as exc:
            logger.exception("agent_execution_failed", user_id=user.user_id)
            raise AgentExecutionError(f"Agent failed: {exc}") from exc

    async def _load_tools(
        self,
        user: UserContext,
        token: str,
        conversation_id: str,
    ) -> list[StructuredTool]:
        if self._permission_service:
            return await self._permission_service.load_agent_tools(
                user, token=token, trace_id=get_trace_id(), conversation_id=conversation_id
            )
        return self._tool_service.load_langchain_tools(
            user.model_copy(update={"permissions": user.effective_permissions}),
            token=token,
            trace_id=get_trace_id(),
            conversation_id=conversation_id,
        )

    async def _execute(
        self,
        message: str,
        user: UserContext,
        tools: list[StructuredTool],
        conversation_id: str,
    ) -> AgentResult:
        agent = self._factory.create_agent(tools)
        parser = self._factory.get_parser()
        memory = self._factory.get_memory()

        system_prompt = self._factory.build_system_prompt(
            user_display_name=user.display_name,
            available_tools=[t.name for t in tools],
        )

        history = await memory.load(conversation_id) if self._config.enable_memory else []
        messages = self._factory._prompt_builder.build_messages(
            message, system_prompt=system_prompt, history=history
        )

        logger.info(
            "agent_executing",
            user_id=user.user_id,
            conversation_id=conversation_id,
            tool_count=len(tools),
            model=self._config.model_name,
        )

        raw = await agent.ainvoke(
            {"messages": messages},
            config={"recursion_limit": self._config.max_iterations},
        )

        if self._config.enable_memory:
            await memory.save(conversation_id, raw.get("messages", []))

        return parser.parse(
            raw,
            conversation_id=conversation_id,
            provider=self.provider_name,
            model=self._config.model_name,
        )
