"""No-op vector store when RAG is disabled."""

from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


class NoOpVectorStore:
    async def search(self, query: str, *, limit: int = 5) -> list[dict[str, Any]]:
        logger.debug("vector_search_skipped", query=query[:50])
        return []

    async def upsert(self, documents: list[dict[str, Any]]) -> None:
        logger.debug("vector_upsert_skipped", count=len(documents))
