"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from src.api.dependencies import close_redis, get_redis
from src.api.routes import router
from src.database import close_db, init_db
from src.utils.correlation import CorrelationIdMiddleware
from src.utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan context (startup/shutdown).

    Args:
        app: FastAPI app instance

    Yields:
        None
    """
    # Startup
    logger.info("Starting notification service...")

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Initialize Redis (via dependency)
    await get_redis()
    logger.info("Redis connection established")

    yield

    # Shutdown
    logger.info("Shutting down notification service...")
    await close_redis()
    await close_db()
    logger.info("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Notification Service",
    description="Multi-channel notification delivery with fallback",
    version="0.1.0",
    lifespan=lifespan,
)

# Add middleware
app.add_middleware(CorrelationIdMiddleware)

# Include routes
app.include_router(router)


if __name__ == "__main__":
    import uvicorn

    from src.config import settings

    uvicorn.run(
        "src.main:app",
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level.lower(),
        reload=True,
    )

