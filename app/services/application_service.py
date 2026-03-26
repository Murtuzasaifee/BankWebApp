"""
Application service — creates and manages application records in the applications table.

Friendly ID format:
  loan     → LOAN-000001
  savings  → SAV-000001
  stock    → STK-000001
"""

from typing import Optional
from app.db.connection import execute_query, execute_command

_ID_PREFIX = {
    "loan":    "LOAN",
    "savings": "SAV",
    "stock":   "STK",
}

# Statuses that can be set by the system (via API sync) vs admin actions
_SYSTEM_STATUSES = {"In Progress", "Pending", "Submitted"}
_ADMIN_STATUSES   = {"Approved", "Rejected"}
_ALLOWED_STATUSES = _SYSTEM_STATUSES | _ADMIN_STATUSES

# API status string → DB status string
_API_STATUS_MAP = {
    "IN_PROGRESS": "In Progress",
    "FAILED":      "Pending",
    "COMPLETED":   "Submitted",
}


def _generate_application_id(service_type: str) -> str:
    """Generate the next friendly application ID for the given service type."""
    prefix = _ID_PREFIX.get(service_type, "APP")
    rows = execute_query(
        "SELECT application_id FROM applications "
        "WHERE application_id LIKE %s ORDER BY id DESC LIMIT 1",
        (f"{prefix}-%",),
    )
    last_seq = int(rows[0]["application_id"].split("-")[1]) if rows else 0
    return f"{prefix}-{last_seq + 1:06d}"


def create_application(
    service_type: str,
    service_name: str,
    trace_id: str,
    user_id: Optional[str] = None,
    username: Optional[str] = None,
    display_name: Optional[str] = None,
    comments: Optional[str] = None,
) -> str:
    """
    Insert a new application record and return the friendly application_id.
    Retries up to 3 times on unique-constraint collision (rare race condition).
    """
    from psycopg.errors import UniqueViolation

    for attempt in range(3):
        application_id = _generate_application_id(service_type)
        try:
            execute_command(
                """
                INSERT INTO applications
                    (application_id, trace_id, user_id, username, display_name,
                     service_type, service_name, status, admin_comments)
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s, 'In Progress', %s)
                """,
                (application_id, trace_id, user_id, username, display_name,
                 service_type, service_name, comments),
            )
            return application_id
        except UniqueViolation:
            if attempt == 2:
                raise
            continue


def get_applications(
    user_id: Optional[str] = None,
    service_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 200,
) -> list[dict]:
    """
    Return applications ordered by created_at DESC.
    Filters by user_id (user-facing view), service_type, or status as needed.
    Never returns trace_id.
    """
    conditions = []
    params = []

    if user_id is not None:
        conditions.append("user_id = %s")
        params.append(user_id)
    if service_type is not None:
        conditions.append("service_type = %s")
        params.append(service_type)
    if status is not None:
        conditions.append("status = %s")
        params.append(status)

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    params.append(limit)

    rows = execute_query(
        f"""
        SELECT application_id, user_id, username, display_name,
               service_type, service_name, status, admin_comments,
               created_at, updated_at
        FROM applications
        {where}
        ORDER BY created_at DESC
        LIMIT %s
        """,
        tuple(params),
    )

    for row in rows:
        if row.get("created_at") and hasattr(row["created_at"], "isoformat"):
            row["created_at"] = row["created_at"].isoformat()
        if row.get("updated_at") and hasattr(row["updated_at"], "isoformat"):
            row["updated_at"] = row["updated_at"].isoformat()

    return rows


def get_application_by_trace_id(trace_id: str) -> Optional[dict]:
    """Return a single application record by platform trace_id (GUID)."""
    rows = execute_query(
        """
        SELECT application_id, trace_id, user_id, username, display_name,
               service_type, service_name, status, admin_comments,
               created_at, updated_at
        FROM applications
        WHERE trace_id = %s
        """,
        (trace_id,),
    )
    if not rows:
        return None
    row = rows[0]
    if row.get("created_at") and hasattr(row["created_at"], "isoformat"):
        row["created_at"] = row["created_at"].isoformat()
    if row.get("updated_at") and hasattr(row["updated_at"], "isoformat"):
        row["updated_at"] = row["updated_at"].isoformat()
    return row


def batch_sync_and_fetch(trace_id_to_api_status: dict) -> dict:
    """
    Batch version of sync_status_from_api + get_application_by_trace_id.

    Fetches all records for the given trace IDs in ONE SELECT query, then issues
    individual UPDATEs only for records whose status needs to change (and that are
    not already in an admin-set terminal state).

    Args:
        trace_id_to_api_status: mapping of trace_id → raw API status string (e.g. 'COMPLETED')

    Returns:
        Dict keyed by trace_id with the full DB record (including resolved status).
        Trace IDs not found in the DB are absent from the result.
    """
    if not trace_id_to_api_status:
        return {}

    trace_ids = list(trace_id_to_api_status.keys())
    rows = execute_query(
        """
        SELECT application_id, trace_id, user_id, username, display_name,
               service_type, service_name, status, admin_comments,
               created_at, updated_at
        FROM applications
        WHERE trace_id = ANY(%s)
        """,
        (trace_ids,),
    )

    db_records: dict = {}
    for row in rows:
        for col in ("created_at", "updated_at"):
            if row.get(col) and hasattr(row[col], "isoformat"):
                row[col] = row[col].isoformat()
        db_records[row["trace_id"]] = row

    # Sync statuses — one UPDATE per record that actually needs it
    for trace_id, api_status_raw in trace_id_to_api_status.items():
        record = db_records.get(trace_id)
        if record is None:
            continue
        current_status = record["status"]
        if current_status in _ADMIN_STATUSES:
            continue  # never overwrite admin decisions
        mapped = _API_STATUS_MAP.get(api_status_raw.upper(), "Pending")
        if current_status != mapped:
            execute_command(
                "UPDATE applications SET status = %s, updated_at = NOW() WHERE trace_id = %s",
                (mapped, trace_id),
            )
            record["status"] = mapped

    return db_records


def sync_status_from_api(trace_id: str, api_status_raw: str) -> Optional[str]:
    """
    Sync DB status for an application based on the API-returned status string.
    Only updates if the current DB status is NOT already Approved or Rejected
    (admin decisions are never overwritten by API sync).

    Returns the resolved status string, or None if no DB record exists.
    """
    mapped = _API_STATUS_MAP.get(api_status_raw.upper(), "Pending")
    rows = execute_query(
        "SELECT application_id, status FROM applications WHERE trace_id = %s",
        (trace_id,),
    )
    if not rows:
        return None
    current_status = rows[0]["status"]
    # Don't overwrite admin decisions
    if current_status in _ADMIN_STATUSES:
        return current_status
    if current_status != mapped:
        execute_command(
            "UPDATE applications SET status = %s, updated_at = NOW() WHERE trace_id = %s",
            (mapped, trace_id),
        )
    return mapped


def get_application_by_id(application_id: str) -> Optional[dict]:
    """
    Return a single application record by friendly application_id.
    Includes trace_id (for admin-only use — do not expose to end users).
    """
    rows = execute_query(
        """
        SELECT application_id, trace_id, user_id, username, display_name,
               service_type, service_name, status, admin_comments,
               created_at, updated_at
        FROM applications
        WHERE application_id = %s
        """,
        (application_id,),
    )
    if not rows:
        return None
    row = rows[0]
    if row.get("created_at") and hasattr(row["created_at"], "isoformat"):
        row["created_at"] = row["created_at"].isoformat()
    if row.get("updated_at") and hasattr(row["updated_at"], "isoformat"):
        row["updated_at"] = row["updated_at"].isoformat()
    return row


def update_application_status(
    application_id: str,
    status: str,
    admin_comments: Optional[str] = None,
) -> bool:
    """
    Update the status (and optionally admin_comments) of an application.
    Returns True if a row was updated, False if application_id not found.
    Raises ValueError for invalid status values.
    """
    if status not in _ADMIN_STATUSES:
        raise ValueError(f"Invalid status '{status}'. Admin can only set: {_ADMIN_STATUSES}")

    execute_command(
        """
        UPDATE applications
        SET status = %s,
            admin_comments = COALESCE(%s, admin_comments),
            updated_at = NOW()
        WHERE application_id = %s
        """,
        (status, admin_comments, application_id),
    )
    # Verify the row exists by fetching it
    rows = execute_query(
        "SELECT application_id FROM applications WHERE application_id = %s",
        (application_id,),
    )
    return len(rows) > 0


def get_application_stats() -> dict:
    """
    Return counts grouped by status for the admin dashboard.
    Returns: {'In Progress': N, 'Pending': N, 'Submitted': N, 'Approved': N, 'Rejected': N, 'total': N}
    """
    rows = execute_query(
        "SELECT status, COUNT(*) AS count FROM applications GROUP BY status"
    )
    stats = {s: 0 for s in _ALLOWED_STATUSES}
    for row in rows:
        if row["status"] in stats:
            stats[row["status"]] = int(row["count"])
    stats["total"] = sum(stats.values())
    return stats
