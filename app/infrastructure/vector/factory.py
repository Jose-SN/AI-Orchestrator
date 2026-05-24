"""Vector store factory."""

from app.core.config import Settings, VectorStoreProvider
from app.infrastructure.vector.noop import NoOpVectorStore
from app.infrastructure.vector.qdrant.store import QdrantVectorStore


def create_vector_store(settings: Settings):
    if settings.vector_store_provider == VectorStoreProvider.QDRANT:
        return QdrantVectorStore(settings.qdrant_url, settings.qdrant_collection)
    return NoOpVectorStore()
