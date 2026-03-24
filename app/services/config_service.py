"""
Config Service — in-memory cache for all asset IDs.

All asset IDs (CHATNOW, INTELLICHAT, and every subcategory) are stored in the
`app_config` DB table and loaded once at application startup into a module-level
cache. This means zero DB queries per request for asset ID lookups.

Key naming convention in app_config:
  - Chat agents : chatnow, intellichat
  - Subcategories: <sub_slug with hyphens replaced by underscores>
                   e.g. savings_account, personal_loan, demat_account

Public API:
    load_asset_ids()                          — called once at startup
    get_chatnow_asset_id() -> str             — cached chatnow value
    get_intellichat_asset_id() -> str         — cached intellichat value
    get_subcategory_asset_id(sub_slug) -> str|None — cached subcategory value
    get_all_cached_asset_ids() -> dict        — full cache snapshot (for admin UI)
    reload_asset_ids()                        — re-load from DB (called by admin API)
    update_asset_ids(updates: dict) -> None   — persist to DB then reload cache
"""

from typing import Optional
from app.core.logger import get_logger

logger = get_logger()

# ---------------------------------------------------------------------------
# Module-level cache — populated by load_asset_ids()
# ---------------------------------------------------------------------------

_cache: dict[str, str] = {}

# Key constants for the two chat-agent IDs
_KEY_CHATNOW = "chatnow"
_KEY_INTELLICHAT = "intellichat"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _sub_key(sub_slug: str) -> str:
    """Convert a subcategory slug to an app_config key, e.g. savings-account → savings_account."""
    return sub_slug.replace("-", "_")


def _load_from_db() -> dict[str, str]:
    """Read all rows from app_config and return as a plain dict."""
    from app.db.connection import execute_query
    rows = execute_query("SELECT key, value FROM app_config")
    return {row["key"]: (row["value"] or "") for row in rows}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_asset_ids() -> None:
    """
    Load all asset IDs from the app_config DB table into the in-memory cache.
    Called once during application startup (lifespan).
    Raises a warning if the DB pool is unavailable or the table is empty.
    """
    global _cache

    try:
        from app.db.connection import _pool  # noqa: F401 — check pool exists
        if _pool is None:
            raise RuntimeError("DB pool not initialised")

        db_data = _load_from_db()

        if not db_data:
            logger.warning(
                "app_config table is empty — asset IDs not loaded. "
                "Run: python scripts/migrate_add_app_config.py"
            )
            _cache = {}
        else:
            _cache = db_data

        logger.info(
            f"Asset IDs loaded from app_config — "
            f"chatnow={_cache.get(_KEY_CHATNOW, '')!r}, "
            f"intellichat={_cache.get(_KEY_INTELLICHAT, '')!r}, "
            f"subcategory_count={sum(1 for k in _cache if k not in (_KEY_CHATNOW, _KEY_INTELLICHAT))}"
        )

    except Exception as e:
        _cache = {}
        logger.warning(f"Could not load asset IDs from DB: {e}. Cache is empty.")


def reload_asset_ids() -> None:
    """Re-load all asset IDs from the DB. Called by the admin reload API."""
    load_asset_ids()
    logger.info("Asset ID cache reloaded by admin request.")


def get_chatnow_asset_id() -> str:
    """Return the cached ChatNow asset ID (empty string if not set)."""
    return _cache.get(_KEY_CHATNOW, "")


def get_intellichat_asset_id() -> str:
    """Return the cached IntelliChat asset ID (empty string if not set)."""
    return _cache.get(_KEY_INTELLICHAT, "")


def get_subcategory_asset_id(sub_slug: str) -> Optional[str]:
    """
    Return the cached asset ID for a subcategory slug.
    e.g. get_subcategory_asset_id('savings-account') looks up key 'savings_account'.
    Returns None if not found or the stored value is empty.
    """
    key = _sub_key(sub_slug)
    value = _cache.get(key, "")
    return value if value else None


def get_all_cached_asset_ids() -> dict:
    """
    Return a snapshot of the full cache for the admin UI.

    Structure:
    {
        "chatnow": "...",
        "intellichat": "...",
        "subcategories": [
            {"key": "savings_account", "value": "...", "label": "Savings Account"},
            ...
        ]
    }
    """
    # Keys that are NOT subcategory entries
    agent_keys = {_KEY_CHATNOW, _KEY_INTELLICHAT}

    subcategories = []
    for key, value in sorted(_cache.items()):
        if key not in agent_keys:
            label = key.replace("_", " ").title()
            subcategories.append({"key": key, "value": value, "label": label})

    return {
        "chatnow": _cache.get(_KEY_CHATNOW, ""),
        "intellichat": _cache.get(_KEY_INTELLICHAT, ""),
        "subcategories": subcategories,
    }


def update_asset_ids(updates: dict) -> None:
    """
    Persist a dict of {key: value} pairs to the app_config table and reload the cache.
    Used by the admin API to save changes made via the UI.
    """
    from app.db.connection import execute_command

    for key, value in updates.items():
        execute_command(
            """
            INSERT INTO app_config (key, value, updated_at)
            VALUES (%s, %s, NOW())
            ON CONFLICT (key) DO UPDATE SET
                value      = EXCLUDED.value,
                updated_at = NOW()
            """,
            (key, value or ""),
        )

    reload_asset_ids()
    logger.info(f"Admin updated {len(updates)} asset ID(s) in app_config.")
