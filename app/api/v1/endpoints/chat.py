"""Chat API endpoints."""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.dependencies import get_auth_token, get_chat_service, get_permission_service
from app.application.services.chat_service import ChatService
from app.application.services.permission_service import PermissionService
from app.domain.models.chat import ChatRequest, ChatResponse
from app.domain.models.tool import ToolRegistrySnapshot

router = APIRouter()


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    token: str = Depends(get_auth_token),
    chat_service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    """
    Process a conversational message through the AI orchestrator.

    The agent dynamically loads tools based on the caller's IAM permissions.
    """
    return await chat_service.process_message(request, token)


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    token: str = Depends(get_auth_token),
    chat_service: ChatService = Depends(get_chat_service),
) -> StreamingResponse:
    """
    Streaming chat endpoint (placeholder).

    Returns the full response in a single chunk until native streaming is implemented.
    """

    async def event_generator():
        async for chunk in chat_service.stream_message(request, token):
            yield f"data: {chunk.model_dump_json()}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@router.get("/tools", response_model=ToolRegistrySnapshot)
async def list_available_tools(
    token: str = Depends(get_auth_token),
    permission_service: PermissionService = Depends(get_permission_service),
) -> ToolRegistrySnapshot:
    """Return tools available to the authenticated user based on IAM permissions."""
    user = await permission_service.resolve_user_context(token)
    return permission_service.get_tool_snapshot(user)
