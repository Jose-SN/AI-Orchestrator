"""In-memory TTL cache for IAM permission lookups."""

import asyncio
import hashlib
import time
from dataclasses import dataclass
from typing import Generic, TypeVar

from app.core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


@dataclass
class _CacheEntry(Generic[T]):
    value: T
    expires_at: float


class IAMPermissionCache:
    """Thread-safe async TTL cache keyed by token hash."""

    def __init__(self, ttl_seconds: int = 300) -> None:
        self._ttl = ttl_seconds
        self._store: dict[str, _CacheEntry] = {}
        self._lock = asyncio.Lock()

    @staticmethod
    def _hash_token(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    async def get(self, token: str) -> T | None:
        key = self._hash_token(token)
        async with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            if time.monotonic() > entry.expires_at:
                del self._store[key]
                logger.debug("iam_cache_expired")
                return None
            logger.debug("iam_cache_hit")
            return entry.value

    async def set(self, token: str, value: T) -> None:
        key = self._hash_token(token)
        async with self._lock:
            self._store[key] = _CacheEntry(value=value, expires_at=time.monotonic() + self._ttl)
            logger.debug("iam_cache_set", ttl=self._ttl)

    async def invalidate(self, token: str) -> None:
        key = self._hash_token(token)
        async with self._lock:
            self._store.pop(key, None)

    async def clear(self) -> None:
        async with self._lock:
            self._store.clear()
            logger.info("iam_cache_cleared")

    @property
    def size(self) -> int:
        return len(self._store)
