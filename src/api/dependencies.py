"""FastAPI dependencies (DB session, Redis client, etc.)."""

from collections.abc import AsyncGenerator
import asyncio

import redis.asyncio as aioredis
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.database import get_db

# Global Redis client (initialized in lifespan)
_redis_client: aioredis.Redis | None = None  # type: ignore[type-arg]
# Async lock to guard singleton creation
_redis_lock = asyncio.Lock()


async def get_redis() -> aioredis.Redis:  # type: ignore[type-arg]
    """Dependency to get Redis client.

    The client is created lazily on first use. An async lock ensures that
    concurrent calls during application startup or high load do not create
    multiple client instances, which could lead to resource leaks or
    inconsistent state.
    """
    global _redis_client
    if _redis_client is None:
        async with _redis_lock:
            # Double‑check pattern after acquiring the lock
            if _redis_client is None:
                _redis_client = aioredis.from_url(
                    settings.redis_url, decode_responses=True
                )
    return _redis_client


async def close_redis() -> None:
    """Close Redis client if it was created."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None
