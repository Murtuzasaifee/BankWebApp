"""
Pure FastAPI session manager.

Stores session data server-side in an in-memory dict.
Uses a signed cookie (HMAC-SHA256, stdlib only) to store the session ID on the client.
"""

import uuid
import time
import hmac
import hashlib
import base64
from typing import Dict, Any, Optional, Tuple
from fastapi import Request, Response


class SessionManager:
    """
    Server-side session manager using signed cookies for session ID storage.

    - Session data is stored in-memory (dict keyed by session ID).
    - The session ID + timestamp is signed with HMAC-SHA256 and sent as a cookie.
    - Sessions expire after `max_age` seconds.
    - Uses only Python standard library (hmac, hashlib, base64).
    """

    def __init__(self, secret_key: str, cookie_name: str = "session_id", max_age: int = 3600):
        self.secret_key = secret_key.encode("utf-8")
        self.cookie_name = cookie_name
        self.max_age = max_age  # seconds
        self._store: Dict[str, Dict[str, Any]] = {}
        self._timestamps: Dict[str, float] = {}

    def _sign(self, value: str) -> str:
        """Create HMAC-SHA256 signature for a value."""
        return hmac.new(self.secret_key, value.encode("utf-8"), hashlib.sha256).hexdigest()

    def _sign_session_id(self, session_id: str) -> str:
        """
        Sign a session ID with a timestamp for cookie storage.

        Format: base64(session_id:timestamp):signature
        """
        timestamp = str(int(time.time()))
        payload = f"{session_id}:{timestamp}"
        encoded = base64.urlsafe_b64encode(payload.encode("utf-8")).decode("utf-8")
        signature = self._sign(payload)
        return f"{encoded}.{signature}"

    def _unsign_session_id(self, signed_value: str) -> Optional[str]:
        """
        Verify and extract session ID from signed cookie value.

        Returns None if signature is invalid or session has expired.
        """
        try:
            parts = signed_value.split(".", 1)
            if len(parts) != 2:
                return None

            encoded, signature = parts

            # Decode payload
            payload = base64.urlsafe_b64decode(encoded.encode("utf-8")).decode("utf-8")

            # Verify signature
            expected_signature = self._sign(payload)
            if not hmac.compare_digest(signature, expected_signature):
                return None

            # Parse session_id and timestamp
            payload_parts = payload.rsplit(":", 1)
            if len(payload_parts) != 2:
                return None

            session_id, timestamp_str = payload_parts

            # Check expiry
            try:
                timestamp = int(timestamp_str)
            except ValueError:
                return None

            if time.time() - timestamp > self.max_age:
                return None

            return session_id

        except Exception:
            return None

    def get_session(self, request: Request) -> Tuple[str, Dict[str, Any]]:
        """
        Get the session dict for the current request.

        Returns:
            Tuple of (session_id, session_data_dict)
        """
        signed_cookie = request.cookies.get(self.cookie_name)

        session_id = None
        if signed_cookie:
            session_id = self._unsign_session_id(signed_cookie)

        # If no valid session, create a new one
        if not session_id or session_id not in self._store:
            session_id = str(uuid.uuid4())
            self._store[session_id] = {}
            self._timestamps[session_id] = time.time()

        return session_id, self._store[session_id]

    def save_session(self, response: Response, session_id: str) -> None:
        """
        Save the session cookie on the response.

        Args:
            response: FastAPI Response object
            session_id: The session ID to persist
        """
        self._timestamps[session_id] = time.time()
        signed = self._sign_session_id(session_id)
        response.set_cookie(
            key=self.cookie_name,
            value=signed,
            max_age=self.max_age,
            httponly=True,
            samesite="lax",
        )

    def clear_session(self, session_id: str) -> None:
        """Remove all data from a session."""
        if session_id in self._store:
            self._store[session_id] = {}

    def delete_session(self, response: Response, session_id: str) -> None:
        """Delete a session entirely and clear the cookie."""
        self._store.pop(session_id, None)
        self._timestamps.pop(session_id, None)
        response.delete_cookie(key=self.cookie_name)
