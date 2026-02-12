"""
Authentication routes - login, logout, auth status.
"""

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

from app.models.schemas import LoginRequest
from app.data.demo_data import USERS
from app.core.dependencies import conversation_store, get_session_manager
from app.core.logger import get_logger

router = APIRouter()
logger = get_logger()


@router.post("/login")
def login(body: LoginRequest, request: Request, response: Response):
    """
    Handle user login.

    Validates credentials against demo USERS dict,
    sets session data, and clears existing conversations.
    """
    try:
        sm = get_session_manager()
        session_id, session = sm.get_session(request)

        username = body.username.strip()
        password = body.password.strip()

        # Check if user exists and password matches
        if username in USERS and USERS[username]['password'] == password:
            session['logged_in'] = True
            session['username'] = username
            session['user_data'] = USERS[username]

            # Ensure session has an ID for conversation tracking
            if 'session_id' not in session:
                session['session_id'] = session_id

            # Clear existing conversation entries for this session
            sid = session.get('session_id', session_id)
            keys_to_remove = [k for k in conversation_store.keys() if k.startswith(f"{sid}_")]
            for key in keys_to_remove:
                del conversation_store[key]

            logger.info(f"User logged in: {username}")
            sm.save_session(response, session_id)
            return {"success": True, "message": "Login successful"}
        else:
            logger.warning(f"Failed login attempt for username: {username}")
            return JSONResponse(
                status_code=401,
                content={"success": False, "message": "Invalid username or password"},
            )

    except Exception as e:
        logger.error(f"Error in login endpoint: {e}")
        logger.exception("Login endpoint exception")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "An error occurred during login"},
        )


@router.post("/logout")
def logout(request: Request, response: Response):
    """
    Handle user logout.

    Clears session data and conversation store entries.
    """
    try:
        sm = get_session_manager()
        session_id, session = sm.get_session(request)

        # Clear existing conversation entries for this session
        sid = session.get('session_id', session_id)
        keys_to_remove = [k for k in conversation_store.keys() if k.startswith(f"{sid}_")]
        for key in keys_to_remove:
            del conversation_store[key]

        # Clear session data
        username = session.get('username', 'Unknown')
        session.pop('logged_in', None)
        session.pop('username', None)
        session.pop('user_data', None)

        logger.info(f"User logged out: {username}")
        sm.save_session(response, session_id)
        return {"success": True, "message": "Logout successful"}

    except Exception as e:
        logger.error(f"Error in logout endpoint: {e}")
        logger.exception("Logout endpoint exception")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "An error occurred during logout"},
        )


@router.get("/auth/status")
def auth_status(request: Request, response: Response):
    """
    Get current authentication status.

    Returns logged_in flag, username, and user data.
    """
    sm = get_session_manager()
    session_id, session = sm.get_session(request)

    logged_in = session.get('logged_in', False)
    username = session.get('username', None)
    user_data = session.get('user_data', None)

    sm.save_session(response, session_id)
    return {
        "logged_in": logged_in,
        "username": username,
        "user_data": user_data,
    }
