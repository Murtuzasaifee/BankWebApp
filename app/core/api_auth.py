"""
API key authentication dependency.

Callers must send X-API-ID and X-API-SECRET headers.
"""

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.config import get_settings


def verify_api_key(request: Request):
    """
    FastAPI dependency that validates API key headers.

    Checks X-API-ID and X-API-SECRET against settings.
    Returns None on success, or a 401 JSONResponse on failure.
    """
    settings = get_settings()
    api_id = request.headers.get("X-API-ID")
    api_secret = request.headers.get("X-API-SECRET")

    if api_id != settings.API_ID or api_secret != settings.API_SECRET:
        return JSONResponse(
            status_code=401,
            content={"error": "Invalid or missing API credentials"},
        )
    return None
