"""Redis caching layer."""

import json
from typing import Any, Optional, TypeVar, Callable
from functools import wraps

import redis.asyncio as redis

from config.settings import Settings
from services.monitoring import MetricsRecorder

settings = Settings()

# Global Redis client
_redis_client: Optional[redis.Redis] = None

T = TypeVar("T")


async def get_redis_client() -> redis.Redis:
    """Get or create Redis client.

    Returns:
        Redis async client
    """
    global _redis_client

    if _redis_client is None:
        _redis_client = await redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            encoding="utf8",
        )

    return _redis_client


async def close_redis() -> None:
    """Close Redis connection."""
    global _redis_client

    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None


class CacheManager:
    """Redis cache management."""

    def __init__(self, redis_client: redis.Redis):
        """Initialize cache manager.

        Args:
            redis_client: Redis async client
        """
        self.redis = redis_client

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        try:
            value = await self.redis.get(key)
            if value:
                MetricsRecorder.record_cache_hit("redis")
                return json.loads(value)
            else:
                MetricsRecorder.record_cache_miss("redis")
        except Exception:
            MetricsRecorder.record_cache_miss("redis")

        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = 3600,
    ) -> None:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default: 1 hour)
        """
        try:
            await self.redis.setex(
                key,
                ttl,
                json.dumps(value, default=str),
            )
        except Exception:
            pass  # Fail silently

    async def delete(self, key: str) -> None:
        """Delete from cache.

        Args:
            key: Cache key
        """
        try:
            await self.redis.delete(key)
        except Exception:
            pass

    async def invalidate_pattern(self, pattern: str) -> None:
        """Invalidate cache keys matching pattern.

        Args:
            pattern: Key pattern (e.g., "scenario:*")
        """
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)
        except Exception:
            pass


def cached(ttl: int = 3600, prefix: str = ""):
    """Decorator for caching function results.

    Args:
        ttl: Cache TTL in seconds
        prefix: Cache key prefix

    Returns:
        Decorated function
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            # Generate cache key
            cache_key = f"{prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"

            # Try cache
            redis_client = await get_redis_client()
            cache_manager = CacheManager(redis_client)

            cached_value = await cache_manager.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Call function
            result = await func(*args, **kwargs)

            # Store in cache
            await cache_manager.set(cache_key, result, ttl)

            return result

        return async_wrapper

    return decorator


# Scenario cache TTLs
CACHE_TTL_SCENARIO = 3600  # 1 hour
CACHE_TTL_SIMULATION = 300  # 5 minutes
CACHE_TTL_RESULTS = 300  # 5 minutes
