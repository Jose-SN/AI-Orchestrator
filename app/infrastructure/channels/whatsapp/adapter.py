"""WhatsApp Business API adapter — future channel."""

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class WhatsAppAdapter:
    def __init__(self) -> None:
        self.enabled = settings.whatsapp_enabled
        self.webhook_path = settings.whatsapp_webhook_path

    async def handle_webhook(self, payload: dict) -> dict:
        if not self.enabled:
            return {"status": "disabled"}
        logger.info("whatsapp_webhook_received", keys=list(payload.keys()))
        return {"status": "not_implemented"}
