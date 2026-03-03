"""
Category service — reads categories and subcategories from the DB.

Replaces the static `app/data/categories.py` lookups for runtime use.
`app/data/categories.py` is retained as seed data source only.
"""

from app.db.connection import execute_query


def get_all_categories() -> list[dict]:
    """
    Return all active categories ordered by display_order,
    each with a nested 'subcategories' list.
    """
    categories = execute_query(
        "SELECT id, slug, name, icon, description, display_order "
        "FROM categories WHERE is_active = TRUE ORDER BY display_order"
    )
    for cat in categories:
        cat["subcategories"] = get_subcategories(cat["id"])
    return categories


def get_category_by_slug(slug: str) -> dict | None:
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
    """Return active subcategories for a category, ordered by display_order."""
    return execute_query(
        "SELECT id, slug, name, asset_id, display_order "
        "FROM subcategories WHERE category_id = %s AND is_active = TRUE ORDER BY display_order",
        (category_id,),
    )


def get_asset_id(category_slug: str, subcategory_slug: str) -> str | None:
    """
    Return the asset_id for a specific category + subcategory pair.
    Returns None if either slug is not found or the asset_id is empty.
    """
    rows = execute_query(
        """
        SELECT s.asset_id
        FROM subcategories s
        JOIN categories c ON c.id = s.category_id
        WHERE c.slug = %s AND s.slug = %s
          AND c.is_active = TRUE AND s.is_active = TRUE
        """,
        (category_slug, subcategory_slug),
    )
    if not rows:
        return None
    return rows[0]["asset_id"] or None
