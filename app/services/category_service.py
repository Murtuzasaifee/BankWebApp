"""
Category service — reads categories and subcategories from the DB.

Replaces the static `app/data/categories.py` lookups for runtime use.
`app/data/categories.py` is retained as seed data source only.

Asset ID lookups (get_asset_id) are served from the in-memory config_service
cache (keyed by sub_slug), so no extra DB query is needed per request.
"""

from typing import Optional
from app.db.connection import execute_query


def get_all_categories() -> list[dict]:
    """
    Return all active categories ordered by display_order,
    each with a nested 'subcategories' list (asset_ids overlaid from cache).
    """
    categories = execute_query(
        "SELECT id, slug, name, icon, description, display_order "
        "FROM categories WHERE is_active = TRUE ORDER BY display_order"
    )
    for cat in categories:
        cat["subcategories"] = get_subcategories(cat["id"])
    return categories


def get_category_by_slug(slug: str) -> Optional[dict]:
    """Return a single active category by slug, or None if not found."""
    rows = execute_query(
        "SELECT id, slug, name, icon, description, display_order "
        "FROM categories WHERE slug = %s AND is_active = TRUE",
        (slug,),
    )
    if not rows:
        return None
    cat = rows[0]
    cat["subcategories"] = get_subcategories(cat["id"])
    return cat


def get_subcategories(category_id: int) -> list[dict]:
    """
    Return active subcategories for a category, ordered by display_order.
    The asset_id field is injected from the in-memory config_service cache.
    """
    from app.services.config_service import get_subcategory_asset_id

    rows = execute_query(
        "SELECT id, slug, name, display_order "
        "FROM subcategories WHERE category_id = %s AND is_active = TRUE ORDER BY display_order",
        (category_id,),
    )

    for row in rows:
        row["asset_id"] = get_subcategory_asset_id(row["slug"]) or ""

    return rows


def get_asset_id(category_slug: str, subcategory_slug: str) -> Optional[str]:
    """
    Return the asset_id for a given subcategory slug.
    category_slug is accepted for backward-compat but not used — keys are sub_slug only.
    Reads from the in-memory config_service cache (zero DB hit).
    """
    from app.services.config_service import get_subcategory_asset_id
    return get_subcategory_asset_id(subcategory_slug)
