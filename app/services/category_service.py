"""
Category service — reads categories and subcategories from the DB.

Replaces the static `app/data/categories.py` lookups for runtime use.
`app/data/categories.py` is retained as seed data source only.

Asset ID lookups (get_asset_id) are served from the in-memory config_service
cache, so no extra DB query is needed per request.
"""

from typing import Optional
from app.db.connection import execute_query


def get_all_categories() -> list[dict]:
    """
    Return all active categories ordered by display_order,
    each with a nested 'subcategories' list.
    Asset IDs in the subcategories are overlaid from the live cache.
    """
    categories = execute_query(
        "SELECT id, slug, name, icon, description, display_order "
        "FROM categories WHERE is_active = TRUE ORDER BY display_order"
    )
    for cat in categories:
        cat["subcategories"] = get_subcategories(cat["id"], cat["slug"])
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
    cat["subcategories"] = get_subcategories(cat["id"], cat["slug"])
    return cat


def get_subcategories(category_id: int, category_slug: str = "") -> list[dict]:
    """
    Return active subcategories for a category, ordered by display_order.
    If category_slug is provided, the asset_id field is overlaid from
    the in-memory config_service cache so the caller always sees the live value.
    """
    from app.services.config_service import get_subcategory_asset_id

    rows = execute_query(
        "SELECT id, slug, name, asset_id, display_order "
        "FROM subcategories WHERE category_id = %s AND is_active = TRUE ORDER BY display_order",
        (category_id,),
    )

    if category_slug:
        for row in rows:
            cached = get_subcategory_asset_id(category_slug, row["slug"])
            if cached is not None:
                row["asset_id"] = cached

    return rows


def get_asset_id(category_slug: str, subcategory_slug: str) -> Optional[str]:
    """
    Return the asset_id for a specific category + subcategory pair.

    Reads from the in-memory config_service cache (zero DB hit).
    Returns None if either slug is not found or the asset_id is empty.
    """
    from app.services.config_service import get_subcategory_asset_id
    return get_subcategory_asset_id(category_slug, subcategory_slug)
