"""
Request log service — inserts and reads from the request_logs table.
"""

from typing import Optional
from app.db.connection import execute_query, execute_command


def log_request(
    request_type: str,
    user_id: Optional[str] = None,
    account_type: Optional[str] = None,
    trace_id: Optional[str] = None,
    document_count: int = 0,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    comments: Optional[str] = None,
) -> None:
    """Insert a row into request_logs."""
    execute_command(
        """
        INSERT INTO request_logs
            (user_id, request_type, account_type, trace_id, document_count, ip_address, user_agent, comments)
        VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (user_id, request_type, account_type, trace_id, document_count, ip_address, user_agent, comments),
    )


def get_request_logs(request_type: Optional[str] = None, limit: int = 100) -> list[dict]:
    """Return request logs ordered by newest first, optionally filtered by type."""
    if request_type:
        return execute_query(
            "SELECT id, user_id, request_type, account_type, trace_id, document_count, "
            "status, ip_address, user_agent, comments, created_at "
            "FROM request_logs WHERE request_type = %s ORDER BY created_at DESC LIMIT %s",
            (request_type, limit),
        )
    return execute_query(
        "SELECT id, user_id, request_type, account_type, trace_id, document_count, "
        "status, ip_address, user_agent, comments, created_at "
        "FROM request_logs ORDER BY created_at DESC LIMIT %s",
        (limit,),
    )


def get_request_log_stats() -> list[dict]:
    """Return counts grouped by request_type and status."""
    return execute_query(
        "SELECT request_type, status, COUNT(*) AS count "
        "FROM request_logs GROUP BY request_type, status ORDER BY request_type, status"
    )
