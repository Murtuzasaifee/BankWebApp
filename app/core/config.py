"""
Configuration for Good Bank Chat Application.

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

    # Agent Configuration
    ASSET_VERSION_ID: str = ""
    ASSET_VERSION_ID_LOGGED_IN: str = ""
    LOAN_AGENT_ASSET_ID: str = ""
    AGENT_NAME: str = "Good Bank Support Agent"
    CONVERSATION_NAME: str = "Good Bank Customer Support Chat"
    QUERY_TIMEOUT: int = 60

    # Application Configuration
    ENVIRONMENT: str = "local"  # "local" or "production"
    SECRET_KEY: str = ""
    SERVER_HOST: str = "127.0.0.1"
    SERVER_PORT: int = 8000
    DEBUG_MODE: bool = True

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()


def validate_config(settings: Settings) -> Tuple[bool, Optional[str]]:
    """
    Validate that required configuration values are set.

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not settings.ASSET_VERSION_ID:
        return False, "ASSET_VERSION_ID is required but not set"

    if not settings.API_KEY:
        return False, "API_KEY is required but not set"

    if not settings.PLATFORM_USERNAME or not settings.PLATFORM_PASSWORD:
        return False, "PLATFORM_USERNAME and PLATFORM_PASSWORD are required but not set"

    if not settings.WORKSPACE_ID:
        return False, "WORKSPACE_ID is required but not set"

    if not settings.SECRET_KEY:
        return False, "SECRET_KEY is required but not set"

    return True, None
