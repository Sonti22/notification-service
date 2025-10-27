"""Pytest fixtures for testing."""

import asyncio
from collections.abc import AsyncGenerator, Generator
from typing import Any

import pytest
import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.database import Base


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create in-memory SQLite session for testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session factory
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def redis_client() -> AsyncGenerator[aioredis.Redis, None]:  # type: ignore[type-arg]
    """Create Redis client (real or mock)."""
    # Use fakeredis for testing (or real Redis if available)
    try:
        client = aioredis.from_url("redis://localhost:6379/15", decode_responses=True)
        await client.ping()
        yield client
        await client.flushdb()
        await client.close()
    except Exception:
        # Fallback to mock
        from unittest.mock import AsyncMock

        mock_redis = AsyncMock()
        mock_redis.xadd = AsyncMock(return_value="1-0")
        mock_redis.xreadgroup = AsyncMock(return_value=[])
        yield mock_redis

