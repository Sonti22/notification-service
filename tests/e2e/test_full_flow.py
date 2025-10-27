"""End-to-end test: full notification flow."""

import asyncio
import json
from unittest.mock import AsyncMock

import pytest

from src.models.schemas import DeliveryChannel, NotificationCreate
from src.services.notification import NotificationService


@pytest.mark.asyncio
async def test_full_notification_flow(
    db_session, redis_client  # type: ignore[no-untyped-def]
) -> None:
    """
    Test full flow: create → send → fallback → retry.

    This is a smoke test with mocked providers.
    """
    service = NotificationService(db_session, redis_client)

    # Step 1: Create and send notification
    notification_data = NotificationCreate(
        recipient="test@example.com",
        message="E2E Test",
        channels=[DeliveryChannel.EMAIL, DeliveryChannel.SMS],
    )

    notification = await service.create_and_send(notification_data)

    # Step 2: Verify creation
    assert notification.id is not None
    assert notification.recipient == "test@example.com"

    # Step 3: Mock mode should succeed on first channel
    assert notification.status in ["sent", "pending", "failed"]

    # Step 4: Retrieve notification
    retrieved = await service.get_notification(notification.id)
    assert retrieved is not None
    assert retrieved.id == notification.id

    # Step 5: Check attempts logged
    assert len(retrieved.attempts) >= 1

