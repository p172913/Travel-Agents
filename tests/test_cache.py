import asyncio
import pytest
from shared.cache import cache_get, cache_set, make_cache_key


@pytest.mark.asyncio
async def test_memory_cache_fallback():
    key = make_cache_key("test", "hello")
    await cache_set(key, "world", ttl=60)
    result = await cache_get(key)
    assert result == "world"


def test_cache_key_deterministic():
    k1 = make_cache_key("research", "goa", "july")
    k2 = make_cache_key("research", "goa", "july")
    assert k1 == k2
