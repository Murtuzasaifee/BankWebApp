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
    "COMPLETED": "Completed",
    "IN_PROGRESS": "In Progress",
    "FAILED": "Pending",       # FAILED → Pending bucket
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
        "applicant_name": item.get("initiated_by", "Unknown"),
        "submission_date": _format_start_time(item.get("start_time", "")),
        "status": _STATUS_MAP.get(raw_status, "Pending"),
        "application_type": f"{item.get('total_documents', 0)} doc(s)",
        "duration": _format_duration(item.get("duration")),
        "error_description": item.get("error_description") or "",
        "asset_id": asset_version_id,
    }


def fetch_applications_for_asset(agent_client, settings, asset_id: str) -> List[Dict[str, Any]]:
    """
    Fetch transactions for a specific asset ID.

    Args:
        agent_client: AgentPlatformClient instance (for auth headers/token refresh)
        settings: Application settings (for PLATFORM_BASE_URL, WORKSPACE_ID)
        asset_id: The specific asset version ID to fetch transactions for

    Returns:
        List of normalized application dicts, sorted by submission_date descending.
    """
    if not asset_id or not asset_id.strip():
        logger.warning("Empty asset_id provided — returning empty list")
        return []

    asset_id = asset_id.strip()
    url = f"{settings.PLATFORM_BASE_URL}/assets"
    client = GraphQLClient(url=url, agent_client=agent_client)

    try:
        data = client.execute(get_asset_transactions(asset_id))
        items = (
            data.get("data", {})
            .get("getAssetTransactionDetails", {})
            .get("items", [])
        )
        applications = [_normalize_item(item, asset_id) for item in items]
        logger.info(f"Fetched {len(applications)} transactions for asset {asset_id}")
    except Exception as e:
        logger.error(f"Error fetching asset {asset_id}: {e}")
        return []

    applications.sort(key=lambda x: x.get("submission_date", ""), reverse=True)
    return applications


def compute_stats(applications: List[Dict[str, Any]]) -> dict:
    """Calculate dashboard stats from a list of applications."""
    pending = sum(1 for a in applications if a["status"] == "Pending")
    in_progress = sum(1 for a in applications if a["status"] == "In Progress")
    completed = sum(1 for a in applications if a["status"] == "Completed")
    return {
        "pending": pending,
        "in_progress": in_progress,
        "completed": completed,
        "total": len(applications),
    }
