"""Retry worker for failed notifications (Redis Streams consumer)."""

import asyncio
import json
import signal
from typing import Any

import redis.asyncio as aioredis

from src.config import settings
from src.database import get_session_factory
from src.models.schemas import DeliveryChannel
from src.services.notification import NotificationService
from src.utils.logger import get_logger

logger = get_logger(__name__)

_shutdown_event = asyncio.Event()


def handle_shutdown(sig: int, frame: Any) -> None:
    """Handle graceful shutdown signals."""
    logger.info(f"Received signal {sig}, shutting down...")
    _shutdown_event.set()


async def retry_worker() -> None:
    """Main retry worker loop (consumes Redis Stream)."""
    redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
    session_factory = get_session_factory()

    # Create consumer group (ignore if exists)
    try:
        await redis_client.xgroup_create(
            name=settings.redis_stream_name,
            groupname=settings.redis_consumer_group,
            id="0",
            mkstream=True,
        )
        logger.info(
            f"Consumer group created: {settings.redis_consumer_group}",
            extra={"group": settings.redis_consumer_group},
        )
    except aioredis.ResponseError as e:
        if "BUSYGROUP" not in str(e):
            raise
        logger.info(
            f"Consumer group already exists: {settings.redis_consumer_group}",
            extra={"group": settings.redis_consumer_group},
        )

    consumer_name = f"worker-{asyncio.current_task()}"  # type: ignore[arg-type]

    logger.info("Retry worker started", extra={"consumer": consumer_name})

    while not _shutdown_event.is_set():
        try:
            # Read from stream (block for 1 second)
            messages = await redis_client.xreadgroup(
                groupname=settings.redis_consumer_group,
                consumername=consumer_name,
                streams={settings.redis_stream_name: ">"},
                count=1,
                block=1000,
            )

            if not messages:
                continue

            for stream_name, stream_messages in messages:
                for message_id, message_data in stream_messages:
                    await process_retry_message(
                        redis_client,
                        session_factory,
                        stream_name,
                        message_id,
                        message_data,
                    )

        except asyncio.CancelledError:
            logger.info("Worker cancelled, shutting down...")
            break
        except Exception as e:
            logger.error(f"Worker error: {e}", extra={"error": str(e)})
            await asyncio.sleep(1)

    await redis_client.close()
    logger.info("Retry worker stopped")


async def process_retry_message(
    redis_client: aioredis.Redis,  # type: ignore[type-arg]
    session_factory: Any,
    stream_name: str,
    message_id: str,
    message_data: dict[str, str],
) -> None:
    """
    Process a single retry message from Redis Stream.

    Args:
        redis_client: Redis client
        session_factory: SQLAlchemy session factory
        stream_name: Stream name
        message_id: Message ID
        message_data: Message payload
    """
    try:
        payload = json.loads(message_data["payload"])
        notification_id = payload["notification_id"]
        channels = [DeliveryChannel(ch) for ch in payload["channels"]]
        attempt = payload["attempt"]

        # Exponential backoff delay
        delay = settings.retry_backoff_base ** (attempt - 1)
        logger.info(
            f"Processing retry for {notification_id} after {delay}s",
            extra={
                "notification_id": notification_id,
                "attempt": attempt,
                "delay": delay,
            },
        )
        await asyncio.sleep(delay)

        # Retry delivery
        async with session_factory() as session:
            service = NotificationService(session, redis_client)
            await service.retry_notification(notification_id, channels, attempt)

        # Acknowledge message
        await redis_client.xack(stream_name, settings.redis_consumer_group, message_id)

    except Exception as e:
        logger.error(
            f"Failed to process retry message: {e}",
            extra={"message_id": message_id, "error": str(e)},
        )
        # Do NOT ack (will be retried by another consumer or same)


if __name__ == "__main__":
    # Setup signal handlers
    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)

    # Run worker
    asyncio.run(retry_worker())

