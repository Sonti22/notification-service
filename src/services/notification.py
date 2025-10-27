"""Основной сервис уведомлений с логикой каскадной отправки."""

import json
from datetime import datetime
from uuid import UUID

import redis.asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.config import settings
from src.models.orm import NotificationAttempt, NotificationORM
from src.models.schemas import (
    DeliveryChannel,
    NotificationCreate,
    NotificationStatus,
)
from src.services.providers import (
    EmailProvider,
    INotificationProvider,
    SMSProvider,
    TelegramProvider,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


class NotificationService:
    """Управляет доставкой уведомлений с каскадной отправкой (fallback)."""

    def __init__(
        self,
        db_session: AsyncSession,
        redis_client: aioredis.Redis,  # type: ignore[type-arg]
    ) -> None:
        """
        Инициализация сервиса.

        Args:
            db_session: Асинхронная сессия SQLAlchemy
            redis_client: Redis-клиент для очереди повторов
        """
        self.db = db_session
        self.redis = redis_client

        # Initialize providers
        self.providers: dict[DeliveryChannel, INotificationProvider] = {
            DeliveryChannel.EMAIL: EmailProvider(),
            DeliveryChannel.SMS: SMSProvider(),
            DeliveryChannel.TELEGRAM: TelegramProvider(),
        }

    async def create_and_send(
        self, notification_data: NotificationCreate
    ) -> NotificationORM:
        """
        Create notification and attempt delivery with fallback.

        Args:
            notification_data: Notification details

        Returns:
            NotificationORM: Created notification with attempts
        """
        # Create notification in DB
        notification = NotificationORM(
            recipient=notification_data.recipient,
            message=notification_data.message,
            status=NotificationStatus.PENDING.value,
            metadata=notification_data.metadata,
        )
        self.db.add(notification)
        await self.db.commit()
        await self.db.refresh(notification)

        logger.info(
            f"Notification created: {notification.id}",
            extra={"notification_id": str(notification.id)},
        )

        # Try delivery with fallback
        await self._attempt_delivery(notification, notification_data.channels)

        return notification

    async def _attempt_delivery(
        self,
        notification: NotificationORM,
        channels: list[DeliveryChannel],
    ) -> None:
        """
        Attempt delivery through channels in order (fallback).

        Args:
            notification: Notification ORM instance
            channels: Ordered list of channels to try
        """
        for channel in channels:
            provider = self.providers.get(channel)
            if not provider:
                logger.warning(
                    f"Provider not found for channel: {channel}",
                    extra={"channel": channel.value},
                )
                continue

            try:
                # Attempt delivery
                await provider.send(notification.recipient, notification.message)

                # Log success
                attempt = NotificationAttempt(
                    notification_id=notification.id,
                    channel=channel.value,
                    timestamp=datetime.utcnow(),
                    success=True,
                )
                self.db.add(attempt)

                # Update notification status
                notification.status = NotificationStatus.SENT.value
                notification.channel_used = channel.value
                await self.db.commit()

                logger.info(
                    f"Notification {notification.id} sent via {channel.value}",
                    extra={
                        "notification_id": str(notification.id),
                        "channel": channel.value,
                    },
                )
                return  # Success, exit fallback loop

            except Exception as e:
                # Log failure
                attempt = NotificationAttempt(
                    notification_id=notification.id,
                    channel=channel.value,
                    timestamp=datetime.utcnow(),
                    success=False,
                    error_message=str(e),
                )
                self.db.add(attempt)
                await self.db.commit()

                logger.warning(
                    f"Delivery failed via {channel.value}: {e}",
                    extra={
                        "notification_id": str(notification.id),
                        "channel": channel.value,
                        "error": str(e),
                    },
                )

        # All channels failed → mark as failed and enqueue for retry
        notification.status = NotificationStatus.FAILED.value
        await self.db.commit()

        await self._enqueue_retry(notification.id, channels)

        logger.error(
            f"All delivery channels failed for {notification.id}",
            extra={"notification_id": str(notification.id)},
        )

    async def _enqueue_retry(
        self, notification_id: UUID, channels: list[DeliveryChannel]
    ) -> None:
        """
        Enqueue notification for retry in Redis Stream.

        Args:
            notification_id: Notification UUID
            channels: Channels to retry
        """
        retry_payload = {
            "notification_id": str(notification_id),
            "channels": [ch.value for ch in channels],
            "attempt": 1,
        }

        await self.redis.xadd(
            settings.redis_stream_name,
            {"payload": json.dumps(retry_payload)},
        )

        logger.info(
            f"Enqueued retry for {notification_id}",
            extra={"notification_id": str(notification_id)},
        )

    async def get_notification(self, notification_id: UUID) -> NotificationORM | None:
        """
        Retrieve notification by ID with attempts.

        Args:
            notification_id: Notification UUID

        Returns:
            NotificationORM or None if not found
        """
        stmt = (
            select(NotificationORM)
            .where(NotificationORM.id == notification_id)
            .options(selectinload(NotificationORM.attempts))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def retry_notification(
        self, notification_id: UUID, channels: list[DeliveryChannel], attempt: int
    ) -> None:
        """
        Retry failed notification (called by worker).

        Args:
            notification_id: Notification UUID
            channels: Channels to retry
            attempt: Current retry attempt number
        """
        notification = await self.get_notification(notification_id)
        if not notification:
            logger.error(
                f"Notification not found for retry: {notification_id}",
                extra={"notification_id": str(notification_id)},
            )
            return

        if notification.status == NotificationStatus.SENT.value:
            logger.info(
                f"Notification {notification_id} already sent, skipping retry",
                extra={"notification_id": str(notification_id)},
            )
            return

        logger.info(
            f"Retrying notification {notification_id} (attempt {attempt})",
            extra={"notification_id": str(notification_id), "attempt": attempt},
        )

        # Reset status to pending for retry
        notification.status = NotificationStatus.PENDING.value
        await self.db.commit()

        # Reattempt delivery
        await self._attempt_delivery(notification, channels)

        # If still failed and under max attempts, enqueue again
        if (
            notification.status == NotificationStatus.FAILED.value
            and attempt < settings.max_retry_attempts
        ):
            retry_payload = {
                "notification_id": str(notification_id),
                "channels": [ch.value for ch in channels],
                "attempt": attempt + 1,
            }
            await self.redis.xadd(
                settings.redis_stream_name,
                {"payload": json.dumps(retry_payload)},
            )
            logger.info(
                f"Re-enqueued retry for {notification_id} (attempt {attempt + 1})",
                extra={"notification_id": str(notification_id), "attempt": attempt + 1},
            )

