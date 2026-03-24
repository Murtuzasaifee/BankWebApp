"""
Config Service — in-memory cache for all asset IDs.

All asset IDs (CHATNOW, INTELLICHAT, and every subcategory) are stored in the
`app_config` DB table and loaded once at application startup into a module-level
cache. This means zero DB queries per request for asset ID lookups.

Public API:
    load_asset_ids()                        — called once at startup
    get_chatnow_asset_id() -> str           — cached chatnow value
    get_intellichat_asset_id() -> str       — cached intellichat value
    get_subcategory_asset_id(cat, sub) -> str|None  — cached subcategory value
    get_all_cached_asset_ids() -> dict      — full cache snapshot (for admin UI)
    reload_asset_ids()                      — re-load from DB (called by admin API)
    update_asset_ids(updates: dict) -> None — persist to DB then reload cache
"""

from typing import Optional
from app.core.logger import get_logger

logger = get_logger()

# ---------------------------------------------------------------------------
# Module-level cache — populated by load_asset_ids()
# ---------------------------------------------------------------------------

_cache: dict[str, str] = {}

# Key constants for the two chat-agent IDs
_KEY_CHATNOW = "chatnow_asset_id"
_KEY_INTELLICHAT = "intellichat_asset_id"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _subcategory_key(cat_slug: str, sub_slug: str) -> str:
    return f"asset.{cat_slug}.{sub_slug}"


def _load_from_db() -> dict[str, str]:
    """Read all rows from app_config and return as a plain dict."""
    from app.db.connection import execute_query
    rows = execute_query("SELECT key, value FROM app_config")
    return {row["key"]: (row["value"] or "") for row in rows}


def _fallback_from_env() -> dict[str, str]:
    """Build a minimal cache from .env settings (used when DB is unavailable)."""
    from app.core.config import get_settings
    settings = get_settings()
    cache: dict[str, str] = {
        _KEY_CHATNOW: settings.CHATNOW_ASSET_ID or "",
        _KEY_INTELLICHAT: settings.INTELLICHAT_ASSET_ID or "",
    }
    return cache


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_asset_ids() -> None:
    """
    Load all asset IDs from the app_config DB table into the in-memory cache.

    Falls back to .env values for the two chat-agent IDs if the DB is not
    configured or if the app_config table has no relevant rows yet.

    Called once during application startup (lifespan).
    """
    global _cache

    try:
        from app.db.connection import _pool  # noqa: F401 — check pool exists
        if _pool is None:
            raise RuntimeError("DB pool not initialised")

        db_data = _load_from_db()

        if not db_data:
            # Table exists but is empty — seed defaults from .env
            logger.warning(
                "app_config table is empty. Falling back to .env values. "
                "Run scripts/migrate_add_app_config.py to seed the DB."
            )
            _cache = _fallback_from_env()
        else:
            _cache = db_data
            # If chat agent IDs are missing from DB, supplement from .env
            from app.core.config import get_settings
            settings = get_settings()
            if not _cache.get(_KEY_CHATNOW) and settings.CHATNOW_ASSET_ID:
                _cache[_KEY_CHATNOW] = settings.CHATNOW_ASSET_ID
            if not _cache.get(_KEY_INTELLICHAT) and settings.INTELLICHAT_ASSET_ID:
                _cache[_KEY_INTELLICHAT] = settings.INTELLICHAT_ASSET_ID

        logger.info(
            f"Asset IDs loaded from app_config — "
            f"chatnow={_cache.get(_KEY_CHATNOW, '')!r}, "
            f"intellichat={_cache.get(_KEY_INTELLICHAT, '')!r}, "
            f"subcategories={sum(1 for k in _cache if k.startswith('asset.'))}"
        )

    except Exception as e:
        logger.warning(
            f"Could not load asset IDs from DB ({e}). Falling back to .env values."
        )
        _cache = _fallback_from_env()


def reload_asset_ids() -> None:
    """Re-load all asset IDs from the DB. Called by the admin reload API."""
    load_asset_ids()
    logger.info("Asset ID cache reloaded by admin request.")


def get_chatnow_asset_id() -> str:
    """Return the cached CHATNOW asset ID (empty string if not set)."""
    return _cache.get(_KEY_CHATNOW, "")


def get_intellichat_asset_id() -> str:
    """Return the cached INTELLICHAT asset ID (empty string if not set)."""
    return _cache.get(_KEY_INTELLICHAT, "")


def get_subcategory_asset_id(cat_slug: str, sub_slug: str) -> Optional[str]:
    """
    Return the cached asset ID for a category/subcategory pair.
    Returns None if not found or the stored value is empty.
    """
    key = _subcategory_key(cat_slug, sub_slug)
    value = _cache.get(key, "")
    return value if value else None


def get_all_cached_asset_ids() -> dict:
    """
    Return a snapshot of the full cache for the admin UI.

    Structure:
    {
        "chatnow_asset_id": "...",
        "intellichat_asset_id": "...",
        "subcategories": [
            {"key": "asset.account-opening.savings-account", "value": "...", "label": "account-opening / savings-account"},
            ...
        ]
    }
    """
    subcategories = []
    for key, value in sorted(_cache.items()):
        if key.startswith("asset."):
            parts = key.split(".", 2)  # ["asset", "cat-slug", "sub-slug"]
            label = f"{parts[1]} / {parts[2]}" if len(parts) == 3 else key
            subcategories.append({"key": key, "value": value, "label": label})

    return {
        "chatnow_asset_id": _cache.get(_KEY_CHATNOW, ""),
        "intellichat_asset_id": _cache.get(_KEY_INTELLICHAT, ""),
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
