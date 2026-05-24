"""Application use cases — chat module."""

from collections.abc import AsyncIterator

from app.application.permissions.service import PermissionService
from app.application.ports import AgentPort
from app.core.logging import AuditAction, audit_log, get_logger
from app.core.observability.metrics import increment_counter
from app.domain.chat.models import (
    ChatRequest,
    ChatResponse,
    StreamChatChunk,
    ToolInvocation,
    new_conversation_id,
)

logger = get_logger(__name__)


class ChatService:
    """Primary use case: process user messages through the AI agent."""

    def __init__(self, permission_service: PermissionService, agent: AgentPort) -> None:
        self._permissions = permission_service
        self._agent = agent

    async def process_message(self, request: ChatRequest, token: str) -> ChatResponse:
        user = await self._permissions.resolve_user_context(token)
        conversation_id = request.conversation_id or new_conversation_id()

        audit_log(
            AuditAction.CHAT_REQUEST,
            user_id=user.user_id,
            conversation_id=conversation_id,
            metadata={"message_length": len(request.message), "agent_id": request.agent_id},
        )
        increment_counter("chat_requests_total", user_id=user.user_id)

        logger.info(
            "chat_request",
            user_id=user.user_id,
            conversation_id=conversation_id,
        )

        snapshot = self._permissions.get_tool_snapshot(user)
        result = await self._agent.run(
            message=request.message,
            user=user,
            token=token,
            conversation_id=conversation_id,
            agent_id=request.agent_id,
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

        for tool in tools_used:
            audit_log(
                AuditAction.TOOL_INVOKED,
                user_id=user.user_id,
                conversation_id=conversation_id,
                resource=tool.tool_name,
                outcome="success" if tool.success else "failure",
            )

        audit_log(
            AuditAction.CHAT_RESPONSE,
            user_id=user.user_id,
            conversation_id=conversation_id,
            metadata={"tools_used": len(tools_used)},
        )

        return ChatResponse(
            conversation_id=conversation_id,
            message=result["response"],
            tools_used=tools_used,
            metadata={
                "user_id": user.user_id,
                "tools_available": snapshot.allowed_tools,
                "llm_provider": result.get("provider"),
                "agent_id": result.get("agent_id"),
            },
        )

    async def stream_message(
        self, request: ChatRequest, token: str
    ) -> AsyncIterator[StreamChatChunk]:
        response = await self.process_message(request, token)
        yield StreamChatChunk(
            conversation_id=response.conversation_id,
            delta=response.message,
            is_final=True,
            metadata={"streaming": False},
        )
