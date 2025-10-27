"""Telegram notification provider (Bot API)."""

import httpx

from src.config import settings
from src.services.providers.base import INotificationProvider
from src.utils.logger import get_logger

logger = get_logger(__name__)


class TelegramProvider(INotificationProvider):
    """Telegram delivery via Bot API."""

    @property
    def channel_name(self) -> str:
        """Return channel name."""
        return "telegram"

    async def send(self, recipient: str, message: str) -> None:
        """
        Send Telegram notification.

        Args:
            recipient: Telegram chat_id or username
            message: Message text

        Raises:
            Exception: If Telegram API fails
        """
        if not settings.is_telegram_configured:
            # Mock mode: log and succeed
            logger.info(
                f"[MOCK] Telegram message sent to {recipient}",
                extra={"recipient": recipient, "provider": "telegram"},
            )
            return

        url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
        data = {
            "chat_id": recipient,
            "text": message,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=data)
                response.raise_for_status()

            logger.info(
                f"Telegram message sent to {recipient}",
                extra={"recipient": recipient, "provider": "telegram"},
            )

        except Exception as e:
            logger.error(
                f"Telegram delivery failed: {e}",
                extra={"recipient": recipient, "provider": "telegram", "error": str(e)},
            )
            raise

