"""SMS notification provider (Twilio)."""

import httpx

from src.config import settings
from src.services.providers.base import INotificationProvider
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SMSProvider(INotificationProvider):
    """SMS delivery via Twilio API."""

    @property
    def channel_name(self) -> str:
        """Return channel name."""
        return "sms"

    async def send(self, recipient: str, message: str) -> None:
        """
        Send SMS notification.

        Args:
            recipient: Phone number (E.164 format)
            message: SMS body

        Raises:
            Exception: If Twilio API fails
        """
        if not settings.is_twilio_configured:
            # Mock mode: log and succeed
            logger.info(
                f"[MOCK] SMS sent to {recipient}",
                extra={"recipient": recipient, "provider": "sms"},
            )
            return

        url = (
            f"https://api.twilio.com/2010-04-01/Accounts/"
            f"{settings.twilio_account_sid}/Messages.json"
        )
        auth = (settings.twilio_account_sid, settings.twilio_auth_token)
        data = {
            "From": settings.twilio_from_number,
            "To": recipient,
            "Body": message,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, auth=auth, data=data)
                response.raise_for_status()

            logger.info(
                f"SMS sent to {recipient}",
                extra={"recipient": recipient, "provider": "sms"},
            )

        except Exception as e:
            logger.error(
                f"SMS delivery failed: {e}",
                extra={"recipient": recipient, "provider": "sms", "error": str(e)},
            )
            raise

