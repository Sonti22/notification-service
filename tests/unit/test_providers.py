"""Unit tests for notification providers."""

import pytest

from src.services.providers import EmailProvider, SMSProvider, TelegramProvider


@pytest.mark.asyncio
async def test_email_provider_mock() -> None:
    """Test email provider in mock mode (no SMTP config)."""
    provider = EmailProvider()
    assert provider.channel_name == "email"

    # Should not raise (mock mode logs and succeeds)
    await provider.send("test@example.com", "Test message")


@pytest.mark.asyncio
async def test_sms_provider_mock() -> None:
    """Test SMS provider in mock mode (no Twilio config)."""
    provider = SMSProvider()
    assert provider.channel_name == "sms"

    # Should not raise (mock mode logs and succeeds)
    await provider.send("+1234567890", "Test message")


@pytest.mark.asyncio
async def test_telegram_provider_mock() -> None:
    """Test Telegram provider in mock mode (no bot token)."""
    provider = TelegramProvider()
    assert provider.channel_name == "telegram"

    # Should not raise (mock mode logs and succeeds)
    await provider.send("123456", "Test message")

