"""
Configuration for ANB Chat Application.

Uses pydantic-settings to load configuration from .env file.
Environment variables override .env values (useful for AWS deployment).
"""

from functools import lru_cache
from typing import Optional, Tuple
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from .env file and environment variables."""

    # AI Agent Platform Credentials
    PLATFORM_BASE_URL: str = "https://api.intellectseecstag.com/magicplatform/v1"
    AUTH_BASE_URL: str = "https://api.intellectseecstag.com/accesstoken"
    TENANT: str = "idxpdemo"
    API_KEY: str = ""
    WORKSPACE_ID: str = ""
    PLATFORM_USERNAME: str = ""
    PLATFORM_PASSWORD: str = ""

    # Application Branding
    APP_NAME: str = "Good Bank"
    APP_THEME: str = "goodbank"
    AGENT_NAME: str = "{APP_NAME} Support Agent"
    CONVERSATION_NAME: str = "{APP_NAME} Customer Support Chat"
    CURRENCY: str = "SAR"
    SUPPORT_EMAIL: str = "customercare@goodbank.com"
    LOCATION: str = "Riyadh, KSA"

    # Agent Configuration
    QUERY_TIMEOUT: int = 60

    # Database Configuration (Supabase Postgres)
    DATABASE_URL: str = ""
    DB_USER: str = ""
    DB_PASSWORD: str = ""
    DB_HOST: str = ""
    DB_PORT: int = 5432
    DB_NAME: str = ""

    # API Authentication
    API_ID: str = ""
    API_SECRET: str = ""

    # Admin Credentials
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin@123"
    ADMIN_DISPLAY_NAME: str = "Administrator"

    # Application Configuration
    ENVIRONMENT: str = "local"  # "local" or "production"
    SECRET_KEY: str = ""
    SERVER_HOST: str = "127.0.0.1"
    SERVER_PORT: int = 8000
    DEBUG_MODE: bool = True
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_ROTATION: str = "10 MB"  # Rotate logs when they reach this size
    LOG_RETENTION: str = "7 days"  # Keep logs for this duration

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",
    }
    
    def __init__(self, **data):
        super().__init__(**data)
        # Failsafe: if deployed to production but host wasn't updated
        if self.ENVIRONMENT == "production":
            if self.SERVER_HOST == "127.0.0.1":
                self.SERVER_HOST = "0.0.0.0"
            # Force debug off in production
            self.DEBUG_MODE = False

    def get_agent_name(self) -> str:
        """Get agent name with fallback to default based on APP_NAME."""
        return self.AGENT_NAME or f"{self.APP_NAME} Support Agent"

    def get_conversation_name(self) -> str:
        """Get conversation name with fallback to default based on APP_NAME."""
        return self.CONVERSATION_NAME or f"{self.APP_NAME} Customer Support Chat"


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()


def validate_config(settings: Settings) -> Tuple[bool, Optional[str]]:
    """
    Validate that required configuration values are set.

    Returns:
        Tuple of (is_valid, error_message)

    Note: CHATNOW_ASSET_ID and INTELLICHAT_ASSET_ID are NOT validated here.
    They can be stored in the app_config DB table and loaded at runtime,
    so their absence from .env is acceptable.
    """
    if not settings.API_KEY:
        return False, "API_KEY is required but not set"

    if not settings.PLATFORM_USERNAME or not settings.PLATFORM_PASSWORD:
        return False, "PLATFORM_USERNAME and PLATFORM_PASSWORD are required but not set"

    if not settings.WORKSPACE_ID:
        return False, "WORKSPACE_ID is required but not set"

    if not settings.SECRET_KEY:
        return False, "SECRET_KEY is required but not set"

    return True, None
