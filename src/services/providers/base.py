"""Base interface for notification providers."""

from abc import ABC, abstractmethod


class INotificationProvider(ABC):
    """Interface for notification delivery providers."""

    @abstractmethod
    async def send(self, recipient: str, message: str) -> None:
        """
        Send notification to recipient.

        Args:
            recipient: Recipient identifier (email, phone, user_id)
            message: Message content

        Raises:
            Exception: If delivery fails
        """
        pass

    @property
    @abstractmethod
    def channel_name(self) -> str:
        """Return channel name (email, sms, telegram)."""
        pass

