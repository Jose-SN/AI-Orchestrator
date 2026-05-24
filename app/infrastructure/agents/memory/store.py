"""Conversation memory — placeholder for future multi-turn support."""

from langchain_core.messages import BaseMessage

from app.core.logging import get_logger

logger = get_logger(__name__)


class ConversationMemoryStore:
    """
    In-memory conversation history stub.

    Replace with Redis/PostgreSQL-backed store when memory is enabled.
    """

    def __init__(self) -> None:
        self._store: dict[str, list[BaseMessage]] = {}

    async def load(self, conversation_id: str) -> list[BaseMessage]:
        logger.debug("memory_load", conversation_id=conversation_id)
        return list(self._store.get(conversation_id, []))

    async def save(self, conversation_id: str, messages: list[BaseMessage]) -> None:
        self._store[conversation_id] = list(messages)
        logger.debug("memory_save", conversation_id=conversation_id, count=len(messages))

    async def clear(self, conversation_id: str) -> None:
        self._store.pop(conversation_id, None)
