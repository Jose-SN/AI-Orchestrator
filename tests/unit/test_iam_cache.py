"""IAM permission cache tests."""

import asyncio

import pytest

from app.domain.auth.models import UserContext
from app.infrastructure.iam.cache import IAMPermissionCache


@pytest.mark.asyncio
async def test_cache_hit_and_miss():
    cache = IAMPermissionCache(ttl_seconds=60)
    user = UserContext(user_id="u1", permissions=["read"])

    assert await cache.get("token-abc") is None
    await cache.set("token-abc", user)
    assert (await cache.get("token-abc")).user_id == "u1"


@pytest.mark.asyncio
async def test_cache_invalidate():
    cache = IAMPermissionCache(ttl_seconds=60)
    user = UserContext(user_id="u1")
    await cache.set("token-xyz", user)
    await cache.invalidate("token-xyz")
    assert await cache.get("token-xyz") is None


@pytest.mark.asyncio
async def test_cache_expiry():
    cache = IAMPermissionCache(ttl_seconds=0)
    await cache.set("token", UserContext(user_id="u1"))
    await asyncio.sleep(0.01)
    assert await cache.get("token") is None
