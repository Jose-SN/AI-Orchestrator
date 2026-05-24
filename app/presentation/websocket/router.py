"""WebSocket route registration."""

from fastapi import FastAPI, WebSocket

from app.core.logging import get_logger
from app.infrastructure.channels.websocket.handler import WebSocketChatHandler

logger = get_logger(__name__)
_handler = WebSocketChatHandler()


def register_websocket_routes(app: FastAPI) -> None:
    @app.websocket("/ws/chat")
    async def websocket_chat(websocket: WebSocket):
        await websocket.accept()
        logger.info("websocket_connected")
        await websocket.send_json({"status": "not_implemented", "message": "WebSocket chat coming soon"})
