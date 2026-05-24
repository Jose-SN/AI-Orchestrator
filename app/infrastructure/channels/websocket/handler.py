"""WebSocket channel handler — future real-time chat."""

from app.core.logging import get_logger

logger = get_logger(__name__)


class WebSocketChatHandler:
    """Placeholder for WebSocket-based streaming chat."""

    async def handle_connection(self, websocket, token: str) -> None:
        logger.info("websocket_connection_placeholder")
        raise NotImplementedError("WebSocket chat not yet implemented")
