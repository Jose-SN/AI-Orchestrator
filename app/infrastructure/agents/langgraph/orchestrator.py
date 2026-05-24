"""LangGraph ReAct agent — permission-filtered tool calling."""

from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent

from app.core.config import settings
from app.core.exceptions import AgentExecutionError
from app.core.logging import get_logger
from app.domain.auth.models import UserContext
from app.domain.prompts.system import ORCHESTRATOR_SYSTEM_PROMPT
from app.infrastructure.llm.factory import create_llm_provider
from app.infrastructure.tools.registry import tool_registry

logger = get_logger(__name__)


class LangGraphOrchestratorAgent:
    """LangChain ReAct agent — never accesses databases, only HTTP tools."""

    def __init__(self) -> None:
        self._llm_provider = create_llm_provider()

    @property
    def provider_name(self) -> str:
        return self._llm_provider.provider_name

    async def run(
        self,
        *,
        message: str,
        user: UserContext,
        token: str,
        conversation_id: str,
    ) -> dict[str, Any]:
        tools = tool_registry.to_langchain_tools(
            user.permissions, token=token, user_id=user.user_id
        )

        if not tools:
            return {
                "response": (
                    "I don't have any tools available for your account permissions. "
                    "Please contact your administrator if you believe this is an error."
                ),
                "tool_invocations": [],
                "provider": self.provider_name,
                "conversation_id": conversation_id,
            }

        try:
            llm = self._llm_provider.get_chat_model()
            agent = create_react_agent(llm, tools)

            system_content = ORCHESTRATOR_SYSTEM_PROMPT
            if user.display_name:
                system_content += f"\n\nYou are assisting: {user.display_name}."

            result = await agent.ainvoke(
                {"messages": [SystemMessage(content=system_content), HumanMessage(content=message)]},
                config={"recursion_limit": settings.agent_max_iterations},
            )

            response_text, tool_invocations = self._extract_result(result)
            return {
                "response": response_text,
                "tool_invocations": tool_invocations,
                "provider": self.provider_name,
                "conversation_id": conversation_id,
            }
        except Exception as exc:
            logger.exception("agent_execution_failed", user_id=user.user_id)
            raise AgentExecutionError(f"Agent failed: {exc}") from exc

    @staticmethod
    def _extract_result(result: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
        messages = result.get("messages", [])
        tool_invocations: list[dict[str, Any]] = []
        response_text = ""

        for msg in messages:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for call in msg.tool_calls:
                    tool_invocations.append({
                        "tool_name": call.get("name", "unknown"),
                        "input": call.get("args", {}),
                        "success": True,
                    })
            if isinstance(msg, AIMessage) and msg.content and not getattr(msg, "tool_calls", None):
                content = msg.content
                response_text = content if isinstance(content, str) else str(content)

        if not response_text and messages:
            last = messages[-1]
            content = getattr(last, "content", "")
            response_text = content if isinstance(content, str) else str(content)

        return response_text, tool_invocations
