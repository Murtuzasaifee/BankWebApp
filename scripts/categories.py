"""
Application Categories configuration.
Maps visual categories to IntellectSee asset IDs.
"""

CATEGORIES = [
    {
        "slug": "account-opening",
        "name": "Account Opening",
        "icon": "fa-university",
        "description": "Current, Savings & Stock Trading Accounts",
        "asset_id": "d252aeb6-6e5f-4476-bdbb-00c95475eb12",
    },
    {
        "slug": "loan-application",
        "name": "Loan Application",
        "icon": "fa-hand-holding-usd",
        "description": "Personal, home & auto loans",
        "asset_id": "f2b35ae2-32a6-4ffe-9a57-ddcf6a2b88c1",
    },
    {
        "slug": "credit-cards",
        "name": "Credit Cards",
        "icon": "fa-credit-card",
        "description": "Credit card applications",
        "asset_id": "",  # To be configured
    },
]

def get_category_by_slug(slug: str) -> dict | None:
    """Return category dict by slug, or None if not found."""
    for cat in CATEGORIES:
        if cat["slug"] == slug:
            return cat
    return None
