"""
Chat route - handles chat messages from the UI.
"""

import uuid
import traceback
from typing import Optional

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

from app.models.schemas import ChatRequest
from app.core.config import get_settings
from app.core.dependencies import conversation_store, get_agent_client, get_session_manager
from app.core.logger import get_logger
from app.services.config_service import get_chatnow_asset_id, get_intellichat_asset_id

router = APIRouter()
logger = get_logger()


def get_or_create_conversation(session_id: str, asset_version_id: Optional[str] = None) -> Optional[str]:
    """
    Get existing conversation ID for session or create a new one.

    Args:
        session_id: Unique session identifier
        asset_version_id: Asset version ID to use

    Returns:
        Conversation ID or None if creation fails
    """
    settings = get_settings()
    agent_client = get_agent_client()

    if asset_version_id is None:
        asset_version_id = get_chatnow_asset_id()

    # Check if we have an existing conversation for this session
    conversation_key = f"{session_id}_{asset_version_id}"
    if conversation_key in conversation_store:
        return conversation_store[conversation_key]

    # Create new conversation
    if not asset_version_id:
        logger.warning("chatnow_asset_id not set. Cannot create conversation.")
        return None

    conversation_id = agent_client.create_conversation(
        asset_version_id=asset_version_id,
        conversation_name=settings.get_conversation_name(),
    )

    if conversation_id:
        conversation_store[conversation_key] = conversation_id
        logger.info(f"Created new conversation {conversation_id} for session {session_id} with asset {asset_version_id}")

    return conversation_id


@router.post("/chat")
def chat(body: ChatRequest, request: Request, response: Response):
    """
    Handle chat messages from the UI.

    Sends user query to the AI agent and returns the response.
    Uses different asset versions for guest vs logged-in users.
    """
    try:
        settings = get_settings()
        agent_client = get_agent_client()
        sm = get_session_manager()
        session_id, session = sm.get_session(request)

        query = body.last_query.strip()

        if not query:
            return JSONResponse(
                status_code=400,
                content={"error": "Empty query", "response": "Please enter a message."},
            )

        # Ensure session has an ID for conversation tracking
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())
        sid = session['session_id']

        # Determine which asset version ID to use based on login status
        is_logged_in = session.get('logged_in', False)
        asset_version_id = get_intellichat_asset_id() if is_logged_in else get_chatnow_asset_id()

        # Get or create conversation with appropriate asset ID
        conversation_id = get_or_create_conversation(sid, asset_version_id)

        if not conversation_id:
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Failed to create conversation",
                    "response": "I'm sorry, I'm having trouble starting a conversation. Please check the configuration.",
                },
            )

        logger.info(f"[Chat] Session: {sid}, Conversation: {conversation_id}, Query: {query[:100]}...")

        # Send query to agent
        response_text, success = agent_client.send_query(
            conversation_id=conversation_id,
            query=query,
            timeout=settings.QUERY_TIMEOUT,
        )

        if not success or not response_text:
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Failed to get response from agent",
                    "response": "I'm sorry, I'm having trouble processing your request. Please try again later.",
                },
            )

        sm.save_session(response, session_id)
        return {
            "response": response_text,
            "agent_name": settings.get_agent_name(),
            "conversation_id": conversation_id,
        }

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        logger.exception("Chat endpoint exception")
        return JSONResponse(
            status_code=500,
            content={
                "error": str(e),
                "response": "I'm sorry, an unexpected error occurred. Please try again.",
            },
        )
