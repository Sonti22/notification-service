"""Unit tests for retry logic."""

import json
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.models.schemas import DeliveryChannel, NotificationStatus
from src.services.notification import NotificationService


@pytest.mark.asyncio
async def test_retry_notification_already_sent(
    db_session, redis_client  # type: ignore[no-untyped-def]
) -> None:
    """Test that retry skips already-sent notifications."""
    from src.models.orm import NotificationORM

    service = NotificationService(db_session, redis_client)

    # Create sent notification
    notification = NotificationORM(
        recipient="test@example.com",
        message="Test",
        status=NotificationStatus.SENT.value,
        channel_used=DeliveryChannel.EMAIL.value,
    )
    db_session.add(notification)
    await db_session.commit()
    await db_session.refresh(notification)

    # Retry should skip
    await service.retry_notification(
        notification.id, [DeliveryChannel.EMAIL], attempt=1
    )

    # Status should remain sent
    await db_session.refresh(notification)
    assert notification.status == NotificationStatus.SENT.value


@pytest.mark.asyncio
async def test_enqueue_retry(db_session, redis_client) -> None:  # type: ignore[no-untyped-def]
    """Test enqueuing notification for retry."""
    service = NotificationService(db_session, redis_client)
    notification_id = uuid4()
    channels = [DeliveryChannel.EMAIL, DeliveryChannel.SMS]

    await service._enqueue_retry(notification_id, channels)

    # Check xadd was called
    if hasattr(redis_client, "xadd"):
        redis_client.xadd.assert_called_once()
        call_args = redis_client.xadd.call_args
        assert call_args[0][0] == "notification:retry"
        payload = json.loads(call_args[0][1]["payload"])
        assert payload["notification_id"] == str(notification_id)
        assert payload["channels"] == ["email", "sms"]
        assert payload["attempt"] == 1

