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
        "chatnow_asset_id": settings.CHATNOW_ASSET_ID if settings.CHATNOW_ASSET_ID else "not configured",
        "intellichat_asset_id": settings.INTELLICHAT_ASSET_ID if settings.INTELLICHAT_ASSET_ID else "not configured"
    }


@router.get("/config")
def get_config():
    """Get current configuration (without sensitive data)."""
    settings = get_settings()
    return {
        "chatnow_asset_id": settings.CHATNOW_ASSET_ID if settings.CHATNOW_ASSET_ID else "not configured",
        "intellichat_asset_id" : settings.INTELLICHAT_ASSET_ID if settings.INTELLICHAT_ASSET_ID else "not configured",
        "app_name": settings.APP_NAME,
        "query_timeout": settings.QUERY_TIMEOUT,
        "conversation_count": len(conversation_store),
    }
