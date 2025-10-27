"""FastAPI routes for notifications API."""

from datetime import datetime
from uuid import UUID

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_redis
from src.database import get_db
from src.models.schemas import (
    AttemptInfo,
    HealthResponse,
    NotificationCreate,
    NotificationResponse,
)
from src.services.notification import NotificationService
from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(status="ok", timestamp=datetime.utcnow())


@router.post(
    "/api/v1/notifications",
    response_model=NotificationResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Notifications"],
)
async def create_notification(
    notification_data: NotificationCreate,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),  # type: ignore[type-arg]
) -> NotificationResponse:
    """
    Create and send a notification.

    Args:
        notification_data: Notification details
        db: Database session
        redis: Redis client

    Returns:
        NotificationResponse with status
    """
    service = NotificationService(db, redis)
    notification = await service.create_and_send(notification_data)

    # Convert to response
    attempts = [
        AttemptInfo(
            channel=att.channel,  # type: ignore[arg-type]
            timestamp=att.timestamp,
            success=att.success,
            error_message=att.error_message,
        )
        for att in notification.attempts
    ]

    return NotificationResponse(
        id=notification.id,
        recipient=notification.recipient,
        message=notification.message,
        status=notification.status,  # type: ignore[arg-type]
        channel_used=notification.channel_used,  # type: ignore[arg-type]
        attempts=attempts,
        created_at=notification.created_at,
        updated_at=notification.updated_at,
    )


@router.get(
    "/api/v1/notifications/{notification_id}",
    response_model=NotificationResponse,
    tags=["Notifications"],
)
async def get_notification(
    notification_id: UUID,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),  # type: ignore[type-arg]
) -> NotificationResponse:
    """
    Get notification status by ID.

    Args:
        notification_id: Notification UUID
        db: Database session
        redis: Redis client

    Returns:
        NotificationResponse

    Raises:
        HTTPException: 404 if not found
    """
    service = NotificationService(db, redis)
    notification = await service.get_notification(notification_id)

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification {notification_id} not found",
        )

    # Convert to response
    attempts = [
        AttemptInfo(
            channel=att.channel,  # type: ignore[arg-type]
            timestamp=att.timestamp,
            success=att.success,
            error_message=att.error_message,
        )
        for att in notification.attempts
    ]

    return NotificationResponse(
        id=notification.id,
        recipient=notification.recipient,
        message=notification.message,
        status=notification.status,  # type: ignore[arg-type]
        channel_used=notification.channel_used,  # type: ignore[arg-type]
        attempts=attempts,
        created_at=notification.created_at,
        updated_at=notification.updated_at,
    )

