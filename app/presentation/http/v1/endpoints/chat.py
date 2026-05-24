from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.application.chat.service import ChatService
from app.application.permissions.service import PermissionService
from app.domain.chat.models import ChatRequest, ChatResponse
from app.domain.tools.models import ToolRegistrySnapshot
from app.presentation.http.dependencies.container import (
    get_auth_token,
    get_chat_service,
    get_permission_service,
)

router = APIRouter()


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    token: str = Depends(get_auth_token),
    chat_service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    return await chat_service.process_message(request, token)


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    token: str = Depends(get_auth_token),
    chat_service: ChatService = Depends(get_chat_service),
) -> StreamingResponse:
    async def event_generator():
        async for chunk in chat_service.stream_message(request, token):
            yield f"data: {chunk.model_dump_json()}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/tools", response_model=ToolRegistrySnapshot)
async def list_available_tools(
    token: str = Depends(get_auth_token),
    permission_service: PermissionService = Depends(get_permission_service),
) -> ToolRegistrySnapshot:
    user = await permission_service.resolve_user_context(token)
    return permission_service.get_tool_snapshot(user)
