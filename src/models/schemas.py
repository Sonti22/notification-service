"""Pydantic schemas for API requests and responses."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class DeliveryChannel(str, Enum):
    """Available notification delivery channels."""

    EMAIL = "email"
    SMS = "sms"
    TELEGRAM = "telegram"


class NotificationStatus(str, Enum):
    """Notification delivery status."""

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class NotificationCreate(BaseModel):
    """Request to create a new notification."""

    recipient: str = Field(..., description="Recipient identifier (email, phone, or user_id)")
    message: str = Field(..., min_length=1, max_length=10000, description="Message content")
    channels: list[DeliveryChannel] = Field(
        default=[DeliveryChannel.EMAIL, DeliveryChannel.SMS, DeliveryChannel.TELEGRAM],
        min_length=1,
        description="Ordered list of channels to try (fallback order)",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional metadata (e.g., template_id, priority)",
    )


class AttemptInfo(BaseModel):
    """Information about a delivery attempt."""

    channel: DeliveryChannel
    timestamp: datetime
    success: bool
    error_message: str | None = None


class NotificationResponse(BaseModel):
    """Response with notification details."""

    id: UUID
    recipient: str
    message: str
    status: NotificationStatus
    channel_used: DeliveryChannel | None = None
    attempts: list[AttemptInfo] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "ok"
    timestamp: datetime = Field(default_factory=datetime.utcnow)

