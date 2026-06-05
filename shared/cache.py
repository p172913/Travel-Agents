"""Redis caching layer with in-memory fallback when Redis is unavailable."""

import hashlib
import json
import logging
from typing import Any, Optional

logger = logging.getLogger("travelsouls.cache")

_redis_client: Any = None
_redis_available: Optional[bool] = None
_memory_cache: dict[str, tuple[str, float]] = {}
_MEMORY_TTL = 3600


def _get_redis():
    global _redis_client, _redis_available
    if _redis_available is False:
        return None
    if _redis_client is not None:
        return _redis_client
    try:
        import redis
        import os

        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        client = redis.from_url(redis_url, decode_responses=True, socket_connect_timeout=2)
        client.ping()
        _redis_client = client
        _redis_available = True
        logger.info("Redis cache connected")
        return _redis_client
    except Exception as exc:
        _redis_available = False
        logger.warning("Redis unavailable, using in-memory cache: %s", exc)
        return None


def make_cache_key(prefix: str, *parts: str) -> str:
    raw = ":".join(str(p) for p in parts)
    digest = hashlib.sha256(raw.encode()).hexdigest()[:16]
    return f"travelsouls:{prefix}:{digest}"


async def cache_get(key: str) -> Optional[str]:
    client = _get_redis()
    if client:
        try:
            return client.get(key)
        except Exception as exc:
            logger.warning("Redis get failed: %s", exc)
    entry = _memory_cache.get(key)
    if entry:
        import time
        value, expires = entry
        if time.time() < expires:
            return value
        del _memory_cache[key]
    return None


async def cache_set(key: str, value: str, ttl: int = 3600) -> None:
    client = _get_redis()
    if client:
        try:
            client.setex(key, ttl, value)
            return
        except Exception as exc:
            logger.warning("Redis set failed: %s", exc)
    import time
    _memory_cache[key] = (value, time.time() + ttl)


async def cached_json(prefix: str, parts: tuple, ttl: int, fetcher):
    """Return cached JSON or call fetcher and cache the result."""
    key = make_cache_key(prefix, *parts)
    cached = await cache_get(key)
    if cached:
        return json.loads(cached)
    result = await fetcher()
    if hasattr(result, "model_dump"):
        payload = result.model_dump()
    elif isinstance(result, dict):
        payload = result
    else:
        payload = result
    await cache_set(key, json.dumps(payload), ttl=ttl)
    return payload
