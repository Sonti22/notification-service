"""Configuration management using pydantic-settings."""

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API
    api_host: str = Field(default="0.0.0.0", description="API bind host")
    api_port: int = Field(default=8000, description="API bind port")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Logging level"
    )

    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./notifications.db",
        description="SQLAlchemy async database URL",
    )

    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0", description="Redis connection URL"
    )
    redis_stream_name: str = Field(
        default="notification:retry", description="Redis stream for retry queue"
    )
    redis_consumer_group: str = Field(
        default="notification-workers", description="Redis consumer group name"
    )

    # Retry
    max_retry_attempts: int = Field(
        default=3, ge=1, le=10, description="Maximum retry attempts"
    )
    retry_backoff_base: float = Field(
        default=2.0, ge=1.0, description="Exponential backoff base (seconds)"
    )

    # Email provider (SMTP)
    smtp_host: str = Field(default="", description="SMTP server host")
    smtp_port: int = Field(default=587, description="SMTP server port")
    smtp_user: str = Field(default="", description="SMTP username")
    smtp_password: str = Field(default="", description="SMTP password")
    smtp_from: str = Field(
        default="noreply@example.com", description="From email address"
    )
    smtp_use_tls: bool = Field(default=True, description="Use TLS for SMTP")

    # SMS provider (Twilio)
    twilio_account_sid: str = Field(default="", description="Twilio Account SID")
    twilio_auth_token: str = Field(default="", description="Twilio Auth Token")
    twilio_from_number: str = Field(
        default="", description="Twilio sender phone number"
    )

    # Telegram provider
    telegram_bot_token: str = Field(default="", description="Telegram Bot API token")

    @property
    def is_smtp_configured(self) -> bool:
        """Check if SMTP is configured."""
        return bool(self.smtp_host and self.smtp_user and self.smtp_password)

    @property
    def is_twilio_configured(self) -> bool:
        """Check if Twilio is configured."""
        return bool(
            self.twilio_account_sid
            and self.twilio_auth_token
            and self.twilio_from_number
        )

    @property
    def is_telegram_configured(self) -> bool:
        """Check if Telegram is configured."""
        return bool(self.telegram_bot_token)


# Global settings instance
settings = Settings()

