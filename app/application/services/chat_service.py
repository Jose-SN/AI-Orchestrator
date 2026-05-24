"""Chat orchestration service — coordinates agent execution."""

from collections.abc import AsyncIterator

from app.agents.orchestrator_agent import OrchestratorAgent
from app.core.logging import get_logger
from app.domain.models.chat import (
    ChatRequest,
    ChatResponse,
    StreamChatChunk,
    ToolInvocation,
    new_conversation_id,
)
from app.domain.models.permission import UserContext
from app.application.services.permission_service import PermissionService

logger = get_logger(__name__)


class ChatService:
    """Primary use case: process user messages through the AI agent."""

    def __init__(
        self,
        permission_service: PermissionService,
        agent: OrchestratorAgent,
    ) -> None:
        self._permissions = permission_service
        self._agent = agent

    async def process_message(
        self,
        request: ChatRequest,
        token: str,
    ) -> ChatResponse:
        """Process a chat message: resolve permissions → run agent → return response."""
        user = await self._permissions.resolve_user_context(token)
        conversation_id = request.conversation_id or new_conversation_id()

        logger.info(
            "chat_request",
            user_id=user.user_id,
            conversation_id=conversation_id,
            message_length=len(request.message),
        )

        snapshot = self._permissions.get_tool_snapshot(user)
        result = await self._agent.run(
            message=request.message,
            user=user,
            token=token,
            conversation_id=conversation_id,
        )

        tools_used = [
            ToolInvocation(
                tool_name=inv["tool_name"],
                input=inv.get("input", {}),
                output=inv.get("output"),
                success=inv.get("success", True),
            )
            for inv in result.get("tool_invocations", [])
        ]

        return ChatResponse(
            conversation_id=conversation_id,
            message=result["response"],
            tools_used=tools_used,
            metadata={
                "user_id": user.user_id,
                "tools_available": snapshot.allowed_tools,
                "llm_provider": result.get("provider"),
            },
        )

    async def stream_message(
        self,
        request: ChatRequest,
        token: str,
    ) -> AsyncIterator[StreamChatChunk]:
        """
        Future streaming endpoint — yields incremental response chunks.

        Currently delegates to non-streaming execution; replace with
        agent.astream() when streaming is enabled.
        """
        response = await self.process_message(request, token)
        yield StreamChatChunk(
            conversation_id=response.conversation_id,
            delta=response.message,
            is_final=True,
            metadata={"streaming": False, "note": "Full response — streaming not yet enabled"},
        )
