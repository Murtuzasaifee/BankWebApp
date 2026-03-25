"""
Authentication routes - login, logout, auth status, user profile.
"""

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

from app.models.schemas import LoginRequest
from app.core.dependencies import conversation_store, get_session_manager
from app.core.logger import get_logger
from app.core.api_auth import verify_api_key
from app.services.user_service import get_user_by_credentials, get_user_profile
from app.services.application_service import get_applications

router = APIRouter()
logger = get_logger()


@router.post("/login")
def login(body: LoginRequest, request: Request, response: Response):
    """
    Handle user login.

    Validates credentials against the users DB table,
    sets session data, and clears existing conversations.
    """
    try:
        sm = get_session_manager()
        session_id, session = sm.get_session(request)

        username = body.username.strip()
        password = body.password.strip()

        user_data = get_user_by_credentials(username, password)

        if user_data:
            session['logged_in'] = True
            session['username'] = username
            session['user_data'] = user_data

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


@router.get("/api/users/{user_id}/profile")
def user_profile(user_id: str, request: Request):
    """
    Get user profile by user_id.

    Requires X-API-ID and X-API-SECRET headers.
    Returns all user fields with accounts and transactions (no password).
    """
    # Verify API credentials
    auth_error = verify_api_key(request)
    if auth_error:
        return auth_error

    profile = get_user_profile(user_id)

    if not profile:
        return JSONResponse(
            status_code=404,
            content={"detail": "User not found"},
        )

    return profile


@router.get("/my-applications")
def my_applications(request: Request, response: Response):
    """
    Return the current user's submitted applications.
    Requires an active user session. Never exposes trace_id.
    """
    sm = get_session_manager()
    session_id, session = sm.get_session(request)

    if not session.get("logged_in"):
        return JSONResponse(status_code=401, content={"error": "Authentication required"})

    user_data = session.get("user_data") or {}
    user_id = user_data.get("user_id")

    applications = get_applications(user_id=user_id)

    sm.save_session(response, session_id)
    return {"applications": applications}
