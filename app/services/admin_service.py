"""
Admin Service — fetches asset transaction data from the IntellectSee platform API.

Calls the `getAssetTransactionDetails` GraphQL query for each configured asset ID
in parallel using ThreadPoolExecutor. Transforms raw API data into the normalized
application format used by the admin dashboard.
"""

import requests
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any

from app.core.logger import get_logger

logger = get_logger()

# View URL template — opens transaction detail in the IntellectSee UI
_VIEW_URL_TEMPLATE = (
    "https://us.intellectseecstag.com/purplefabric/assetmonitor"
    "/ws/{workspace_id}/workflow/asset/{asset_id}/transcation/{transaction_id}"
)

# Status mapping: API status → display status
_STATUS_MAP = {
    "COMPLETED": "Completed",
    "IN_PROGRESS": "In Progress",
    "FAILED": "Pending",       # FAILED → Pending bucket
}


def _build_graphql_query(asset_version_id: str) -> dict:
    """Build the GraphQL request body for getAssetTransactionDetails."""
    # Date window: last 30 days
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=30)

    query = """
    query {
      getAssetTransactionDetails(
        asset_version_id: "%s"
        dateFilter: {
          start_date: "%s",
          end_date: "%s"
        }
        pagination: { page: 1, limit: 50 }
        transactionFilters: {
          commonFilters: { status: [], created_by: [] },
          getCurrentUserTransactions: true,
          searchFilter: ""
        }
      ) {
        meta {
          itemCount
          totalItems
          itemsPerPage
          totalPages
          currentPage
        }
        items {
          transaction_id
          initiated_by
          total_documents
          status
          total_pages
          total_pages_processed
          duration {
            days
            hours
            minutes
            seconds
            milliseconds
          }
          start_time
          error_code
          error_description
        }
      }
    }
    """ % (
        asset_version_id,
        start.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        now.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
    )

    return {"query": query}


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


def _fetch_for_asset(
    asset_version_id: str,
    platform_base_url: str,
    workspace_id: str,
    headers: dict,
) -> List[Dict[str, Any]]:
    """
    Fetch transactions for a single asset version ID.
    Returns a list of normalized application dicts.
    """
    body = _build_graphql_query(asset_version_id)
    url = f"{platform_base_url}/assets"

    try:
        resp = requests.post(url, headers=headers, json=body, timeout=30)

        # Token expired — caller should retry at a higher level
        if resp.status_code == 401:
            raise PermissionError("401 — token expired")

        resp.raise_for_status()
        data = resp.json()

        items = (
            data.get("data", {})
            .get("getAssetTransactionDetails", {})
            .get("items", [])
        )

        applications = []
        for item in items:
            raw_status = (item.get("status") or "").upper()
            display_status = _STATUS_MAP.get(raw_status, "Pending")

            applications.append({
                "application_id": item.get("transaction_id", ""),
                "applicant_name": item.get("initiated_by", "Unknown"),
                "submission_date": _format_start_time(item.get("start_time", "")),
                "status": display_status,
                "application_type": f"{item.get('total_documents', 0)} doc(s)",
                "application_html_url": _VIEW_URL_TEMPLATE.format(
                    workspace_id=workspace_id,
                    asset_id=asset_version_id,
                    transaction_id=item.get("transaction_id", ""),
                ),
                "duration": _format_duration(item.get("duration")),
                "error_description": item.get("error_description") or "",
                "asset_id": asset_version_id,
            })

        logger.info(
            f"Fetched {len(applications)} transactions for asset {asset_version_id}"
        )
        return applications

    except PermissionError:
        raise
    except Exception as e:
        logger.error(f"Error fetching asset {asset_version_id}: {e}")
        return []


def fetch_all_applications(agent_client, settings) -> List[Dict[str, Any]]:
    """
    Fetch transactions for all configured asset IDs in parallel.

    Args:
        agent_client: AgentPlatformClient instance (for auth headers/token refresh)
        settings: Application settings (for ADMIN_ASSET_IDS, PLATFORM_BASE_URL, WORKSPACE_ID)

    Returns:
        Combined list of normalized application dicts, sorted by submission_date descending.
    """
    raw_ids = settings.ADMIN_ASSET_IDS or ""
    asset_ids = [aid.strip() for aid in raw_ids.split(",") if aid.strip()]

    if not asset_ids:
        logger.warning("No ADMIN_ASSET_IDS configured — returning empty list")
        return []

    headers = agent_client.get_headers()
    platform_url = settings.PLATFORM_BASE_URL
    workspace_id = settings.WORKSPACE_ID

    all_apps: List[Dict[str, Any]] = []

    def _fetch(aid: str):
        return _fetch_for_asset(aid, platform_url, workspace_id, headers)

    try:
        with ThreadPoolExecutor(max_workers=min(len(asset_ids), 5)) as pool:
            futures = {pool.submit(_fetch, aid): aid for aid in asset_ids}
            for future in as_completed(futures):
                aid = futures[future]
                try:
                    result = future.result()
                    all_apps.extend(result)
                except PermissionError:
                    # Token expired — refresh once and retry all
                    logger.warning("Token expired during fetch, refreshing and retrying...")
                    agent_client.refresh_access_token()
                    return fetch_all_applications(agent_client, settings)
                except Exception as e:
                    logger.error(f"Error processing asset {aid}: {e}")

    except Exception as e:
        logger.error(f"Error in parallel fetch: {e}")

    # Sort by submission_date descending (most recent first)
    all_apps.sort(key=lambda x: x.get("submission_date", ""), reverse=True)
    return all_apps


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
