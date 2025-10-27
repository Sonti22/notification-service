"""Unit tests for NotificationService."""

import pytest
from sqlalchemy import select

from src.models.orm import NotificationORM
from src.models.schemas import DeliveryChannel, NotificationCreate, NotificationStatus
from src.services.notification import NotificationService


@pytest.mark.asyncio
async def test_create_and_send_notification_success(
    db_session, redis_client  # type: ignore[no-untyped-def]
) -> None:
    """Test creating and sending notification (success on first channel)."""
    service = NotificationService(db_session, redis_client)

    notification_data = NotificationCreate(
        recipient="test@example.com",
        message="Hello World",
        channels=[DeliveryChannel.EMAIL],
    )

    notification = await service.create_and_send(notification_data)

    assert notification.id is not None
    assert notification.recipient == "test@example.com"
    assert notification.message == "Hello World"
    assert notification.status == NotificationStatus.SENT.value
    assert notification.channel_used == DeliveryChannel.EMAIL.value

    # Check attempt logged
    assert len(notification.attempts) == 1
    assert notification.attempts[0].success is True
    assert notification.attempts[0].channel == DeliveryChannel.EMAIL.value


@pytest.mark.asyncio
async def test_create_and_send_notification_fallback(
    db_session, redis_client  # type: ignore[no-untyped-def]
) -> None:
    """Test fallback to next channel (all mock providers succeed)."""
    service = NotificationService(db_session, redis_client)

    notification_data = NotificationCreate(
        recipient="test@example.com",
        message="Hello World",
        channels=[DeliveryChannel.EMAIL, DeliveryChannel.SMS],
    )

    notification = await service.create_and_send(notification_data)

    # Mock mode: all succeed, so should succeed on first channel
    assert notification.status == NotificationStatus.SENT.value
    assert notification.channel_used == DeliveryChannel.EMAIL.value


@pytest.mark.asyncio
async def test_get_notification(
    db_session, redis_client  # type: ignore[no-untyped-def]
) -> None:
    """Test retrieving notification by ID."""
    service = NotificationService(db_session, redis_client)

    notification_data = NotificationCreate(
        recipient="test@example.com",
        message="Test",
        channels=[DeliveryChannel.EMAIL],
    )

    created = await service.create_and_send(notification_data)
    retrieved = await service.get_notification(created.id)

    assert retrieved is not None
    assert retrieved.id == created.id
    assert retrieved.recipient == created.recipient


@pytest.mark.asyncio
async def test_get_notification_not_found(
    db_session, redis_client  # type: ignore[no-untyped-def]
) -> None:
    """Test retrieving non-existent notification."""
    from uuid import uuid4

    service = NotificationService(db_session, redis_client)
    notification = await service.get_notification(uuid4())

    assert notification is None

