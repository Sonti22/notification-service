"""Email notification provider (SMTP)."""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from src.config import settings
from src.services.providers.base import INotificationProvider
from src.utils.logger import get_logger

logger = get_logger(__name__)


class EmailProvider(INotificationProvider):
    """Email delivery via SMTP."""

    @property
    def channel_name(self) -> str:
        """Return channel name."""
        return "email"

    async def send(self, recipient: str, message: str) -> None:
        """
        Send email notification.

        Args:
            recipient: Email address
            message: Email body (plain text)

        Raises:
            Exception: If SMTP fails
        """
        if not settings.is_smtp_configured:
            # Mock mode: log and succeed
            logger.info(
                f"[MOCK] Email sent to {recipient}",
                extra={"recipient": recipient, "provider": "email"},
            )
            return

        try:
            # Create message
            msg = MIMEMultipart()
            msg["From"] = settings.smtp_from
            msg["To"] = recipient
            msg["Subject"] = "Notification"
            msg.attach(MIMEText(message, "plain"))

            # Connect and send
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
                if settings.smtp_use_tls:
                    server.starttls()
                server.login(settings.smtp_user, settings.smtp_password)
                server.send_message(msg)

            logger.info(
                f"Email sent to {recipient}",
                extra={"recipient": recipient, "provider": "email"},
            )

        except Exception as e:
            logger.error(
                f"Email delivery failed: {e}",
                extra={"recipient": recipient, "provider": "email", "error": str(e)},
            )
            raise

