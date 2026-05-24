"""Qdrant vector store — future RAG integration."""

from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


class QdrantVectorStore:
    """Placeholder for Qdrant-backed semantic search."""

    def __init__(self, url: str, collection: str) -> None:
        self.url = url
        self.collection = collection

    async def search(self, query: str, *, limit: int = 5) -> list[dict[str, Any]]:
        logger.info("qdrant_search_not_implemented", collection=self.collection)
        return []

    async def upsert(self, documents: list[dict[str, Any]]) -> None:
        logger.info("qdrant_upsert_not_implemented", count=len(documents))
