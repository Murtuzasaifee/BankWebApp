"""
Admin Service — fetches asset transaction data from the IntellectSee platform API.

Calls the `getAssetTransactionDetails` GraphQL query for a specific asset ID.
Transforms raw API data into the normalized application format used by the admin dashboard.
"""

from datetime import datetime
from typing import List, Dict, Any

from app.core.logger import get_logger
from app.services.graphql_client import GraphQLClient
from app.services.admin_queries import get_asset_transactions

logger = get_logger()

# Status mapping: API status → display status
_STATUS_MAP = {
    "COMPLETED":  "Submitted",   # AI processing done → ready for admin action
    "IN_PROGRESS": "In Progress",
    "FAILED":      "Pending",    # FAILED → Pending bucket
}


def _format_start_time(iso_str: str) -> str:
    """Convert ISO 8601 string to human-readable format (e.g. 'Feb 27, 2026 13:04')."""
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%b %d, %Y %H:%M")
    except Exception:
        return iso_str or ""


def _format_duration(dur: dict) -> str:
    """Format duration dict into a short human-readable string."""
    if not dur:
        return "-"
    parts = []
    for unit in ("days", "hours", "minutes", "seconds"):
        val = dur.get(unit)
        if val:
            parts.append(f"{val}{unit[0]}")
    if not parts:
        ms = dur.get("milliseconds")
        if ms:
            parts.append(f"{ms}ms")
    return " ".join(parts) if parts else "-"


def _normalize_item(item: dict, asset_version_id: str) -> dict:
    """Map a raw API transaction item to the application dict format."""
    raw_status = (item.get("status") or "").upper()
    return {
        "application_id": item.get("transaction_id", ""),
        "applicant_name": item.get("initiated_by") or "",
        "submission_date": _format_start_time(item.get("start_time", "")),
        "status": _STATUS_MAP.get(raw_status, "Pending"),
        "application_type": f"{item.get('total_documents', 0)} doc(s)",
        "duration": _format_duration(item.get("duration")),
        "error_description": item.get("error_description") or "",
        "asset_id": asset_version_id,
    }


_EMPTY_PAGINATION = {"current_page": 1, "total_pages": 1, "total_items": 0, "items_per_page": 10}


def fetch_applications_for_asset(
    agent_client, settings, asset_id: str, page: int = 1, limit: int = 50
) -> tuple[List[Dict[str, Any]], dict]:
    """
    Fetch transactions for a specific asset ID.

    Returns:
        Tuple of (applications, pagination_meta).
        pagination_meta keys: current_page, total_pages, total_items, items_per_page.
    """
    if not asset_id or not asset_id.strip():
        logger.warning("Empty asset_id provided — returning empty list")
        return [], _EMPTY_PAGINATION

    asset_id = asset_id.strip()
    url = f"{settings.PLATFORM_BASE_URL}/assets"
    client = GraphQLClient(url=url, agent_client=agent_client)

    try:
        data = client.execute(get_asset_transactions(asset_id, page=page, limit=limit))
        tx_data = data.get("data", {}).get("getAssetTransactionDetails", {})
        items = tx_data.get("items", [])
        raw_meta = tx_data.get("meta", {})
        applications = [_normalize_item(item, asset_id) for item in items]
        logger.info(f"Fetched {len(applications)} transactions (page {page}) for asset {asset_id}")
    except Exception as e:
        logger.error(f"Error fetching asset {asset_id}: {e}")
        return [], _EMPTY_PAGINATION

    pagination = {
        "current_page": raw_meta.get("currentPage", page),
        "total_pages":  raw_meta.get("totalPages", 1),
        "total_items":  raw_meta.get("totalItems", len(applications)),
        "items_per_page": raw_meta.get("itemsPerPage", limit),
    }

    applications.sort(key=lambda x: x.get("submission_date", ""), reverse=True)
    return applications, pagination


def merge_with_db(applications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    For each application fetched from the API, look up the matching DB record by trace_id.
    - Syncs DB status based on API status (skips if already Approved/Rejected).
    - Annotates each application dict with DB fields: db_application_id, display_name, username, db_status.
    - The final 'status' shown is the DB status (which takes precedence for admin actions).
    """
    from app.services.application_service import sync_status_from_api, get_application_by_trace_id

    for app in applications:
        trace_id = app.get("application_id", "")  # in normalized dict, application_id = platform trace GUID
        api_status_raw = ""
        # Reverse-map display status back to raw API status for sync
        _REVERSE = {"Submitted": "COMPLETED", "In Progress": "IN_PROGRESS", "Pending": "FAILED"}
        api_status_raw = _REVERSE.get(app.get("status", ""), "FAILED")

        resolved_status = sync_status_from_api(trace_id, api_status_raw)
        if resolved_status:
            app["status"] = resolved_status

        db_record = get_application_by_trace_id(trace_id)
        if db_record:
            app["db_application_id"] = db_record["application_id"]
            app["display_name"] = db_record.get("display_name") or db_record.get("username") or ""
            app["status"] = db_record["status"]  # DB status is authoritative
        else:
            app["db_application_id"] = ""
            app["display_name"] = app.get("applicant_name", "")

    return applications


def compute_stats(applications: List[Dict[str, Any]]) -> dict:
    """Calculate dashboard stats from a list of applications."""
    pending     = sum(1 for a in applications if a["status"] == "Pending")
    in_progress = sum(1 for a in applications if a["status"] == "In Progress")
    submitted   = sum(1 for a in applications if a["status"] == "Submitted")
    approved    = sum(1 for a in applications if a["status"] == "Approved")
    rejected    = sum(1 for a in applications if a["status"] == "Rejected")
    return {
        "pending":     pending,
        "in_progress": in_progress,
        "submitted":   submitted,
        "approved":    approved,
        "rejected":    rejected,
        "total":       len(applications),
    }
