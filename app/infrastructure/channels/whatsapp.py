"""Future WhatsApp channel adapter (placeholder)."""

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class WhatsAppChannel:
    """
    Placeholder for future WhatsApp Business API integration.

    When enabled, inbound webhook messages will be routed through
    ChatService using the same agent pipeline as the REST API.
    """

    def __init__(self) -> None:
        self.enabled = settings.whatsapp_enabled
        self.webhook_path = settings.whatsapp_webhook_path

    async def handle_webhook(self, payload: dict) -> dict:
        if not self.enabled:
            logger.warning("whatsapp_disabled")
            return {"status": "disabled"}
        # TODO: Parse WhatsApp payload, resolve user token, delegate to ChatService
        logger.info("whatsapp_webhook_received", payload_keys=list(payload.keys()))
        return {"status": "not_implemented"}
