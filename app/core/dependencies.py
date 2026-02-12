"""
Shared dependencies for FastAPI route handlers.
"""

from typing import Dict
from app.core.config import get_settings, Settings
from app.services.query_agent import AgentPlatformClient
from app.core.session import SessionManager

# In-memory conversation store (keyed by "{session_id}_{asset_version_id}")
conversation_store: Dict[str, str] = {}

# Singleton agent client
_agent_client: AgentPlatformClient = None

# Singleton session manager
_session_manager: SessionManager = None


def get_agent_client() -> AgentPlatformClient:
    """Get or create the shared AgentPlatformClient singleton."""
    global _agent_client
    if _agent_client is None:
        settings = get_settings()
        _agent_client = AgentPlatformClient(settings=settings)
    return _agent_client


def get_session_manager() -> SessionManager:
    """Get or create the shared SessionManager singleton."""
    global _session_manager
    if _session_manager is None:
        settings = get_settings()
        _session_manager = SessionManager(secret_key=settings.SECRET_KEY)
    return _session_manager
