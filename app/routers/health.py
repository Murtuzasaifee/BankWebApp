"""
Health and config routes.
"""

from fastapi import APIRouter

from app.core.config import get_settings
from app.core.dependencies import conversation_store, get_agent_client

router = APIRouter()


@router.get("/health")
def health():
    """Health check endpoint."""
    settings = get_settings()
    agent_client = get_agent_client()
    return {
        "status": "healthy",
        "agent_configured": agent_client.access_token is not None,
        "asset_version_id": settings.ASSET_VERSION_ID if settings.ASSET_VERSION_ID else "not configured",
    }


@router.get("/config")
def get_config():
    """Get current configuration (without sensitive data)."""
    settings = get_settings()
    return {
        "asset_version_id": settings.ASSET_VERSION_ID if settings.ASSET_VERSION_ID else "not configured",
        "agent_name": settings.AGENT_NAME,
        "conversation_name": settings.CONVERSATION_NAME,
        "query_timeout": settings.QUERY_TIMEOUT,
        "conversation_count": len(conversation_store),
    }
