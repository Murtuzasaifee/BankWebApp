"""
Seed script — creates and populates the categories and subcategories tables.

Run standalone:
    python scripts/seed_categories.py
"""

import os
import sys

# Allow imports from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.connection import get_connection

# ---------------------------------------------------------------------------
# Seed data
# ---------------------------------------------------------------------------

SEED = [
    {
        "slug": "account-opening",
        "name": "Account Opening",
        "icon": "fa-university",
        "description": "Current, Savings & Demat Accounts",
        "display_order": 1,
        "subcategories": [
            {"slug": "savings-account",  "name": "Savings Account",  "display_order": 1},
            {"slug": "current-account",  "name": "Current Account",  "display_order": 2},
            {"slug": "demat-account",    "name": "Demat Account",    "display_order": 3},
        ],
    },
    {
        "slug": "loan-application",
        "name": "Loan Application",
        "icon": "fa-hand-holding-usd",
        "description": "Personal, home & auto loans",
        "display_order": 2,
        "subcategories": [
            {"slug": "personal-loan", "name": "Personal Loan", "display_order": 1},
            {"slug": "home-loan",     "name": "Home Loan",     "display_order": 2},
            {"slug": "auto-loan",     "name": "Auto Loan",     "display_order": 3},
        ],
    },
    {
        "slug": "credit-cards",
        "name": "Credit Cards",
        "icon": "fa-credit-card",
        "description": "Credit card applications",
        "display_order": 3,
        "subcategories": [
            {"slug": "credit-card-application", "name": "Credit Card Application", "display_order": 1},
        ],
    },
]


# ---------------------------------------------------------------------------
# Schema DDL (categories + subcategories only)
# ---------------------------------------------------------------------------

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS request_logs (
    id              SERIAL PRIMARY KEY,
    user_id         VARCHAR(20),
    request_type    VARCHAR(50) NOT NULL,
    account_type    VARCHAR(50),
    trace_id        VARCHAR(100),
    document_count  INT DEFAULT 0,
    status          VARCHAR(30) DEFAULT 'Submitted',
    ip_address      VARCHAR(45),
    user_agent      TEXT,
    comments        TEXT,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS categories (
    id              SERIAL PRIMARY KEY,
    slug            VARCHAR(50) UNIQUE NOT NULL,
    name            VARCHAR(100) NOT NULL,
    icon            VARCHAR(50) NOT NULL,
    description     TEXT,
    display_order   INT DEFAULT 0,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS subcategories (
    id              SERIAL PRIMARY KEY,
    category_id     INT NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    slug            VARCHAR(50) NOT NULL,
    name            VARCHAR(100) NOT NULL,
    display_order   INT DEFAULT 0,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT NOW(),
    UNIQUE(category_id, slug)
);
"""


# ---------------------------------------------------------------------------
# Seed
# ---------------------------------------------------------------------------

def seed():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Create tables
            cur.execute(SCHEMA_SQL)
            print("Tables ensured: categories, subcategories")

            total_cats = 0
            total_subs = 0

            for cat in SEED:
                subs = cat.pop("subcategories")

                # Upsert category
                cur.execute(
                    """
                    INSERT INTO categories (slug, name, icon, description, display_order)
                    VALUES (%(slug)s, %(name)s, %(icon)s, %(description)s, %(display_order)s)
                    ON CONFLICT (slug) DO UPDATE SET
                        name          = EXCLUDED.name,
                        icon          = EXCLUDED.icon,
                        description   = EXCLUDED.description,
                        display_order = EXCLUDED.display_order
                    RETURNING id
                    """,
                    cat,
                )
                category_id = cur.fetchone()[0]
                total_cats += 1

                # Upsert subcategories
                for sub in subs:
                    cur.execute(
                        """
                        INSERT INTO subcategories (category_id, slug, name, display_order)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (category_id, slug) DO UPDATE SET
                            name          = EXCLUDED.name,
                            display_order = EXCLUDED.display_order
                        """,
                        (category_id, sub["slug"], sub["name"], sub["display_order"]),
                    )
                    total_subs += 1

        conn.commit()
        print(f"Seeded {total_cats} categories and {total_subs} subcategories.")
    finally:
        conn.close()


if __name__ == "__main__":
    seed()
