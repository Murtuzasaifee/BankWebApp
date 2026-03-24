"""
Migration script — creates the app_config table and seeds all asset IDs.

Seeds:
  - chatnow_asset_id      from CHATNOW_ASSET_ID in .env
  - intellichat_asset_id  from INTELLICHAT_ASSET_ID in .env
  - asset.<cat>.<sub>     from every row in the subcategories table

Safe to run multiple times (uses ON CONFLICT DO UPDATE).

Run standalone:
    python scripts/migrate_add_app_config.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.connection import get_connection
from app.core.config import get_settings

# ---------------------------------------------------------------------------
# DDL
# ---------------------------------------------------------------------------

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS app_config (
    key         VARCHAR(100) PRIMARY KEY,
    value       TEXT,
    description TEXT,
    updated_at  TIMESTAMP DEFAULT NOW()
);
"""

UPSERT = """
INSERT INTO app_config (key, value, description)
VALUES (%s, %s, %s)
ON CONFLICT (key) DO UPDATE SET
    value      = EXCLUDED.value,
    description = EXCLUDED.description,
    updated_at  = NOW();
"""


def migrate():
    settings = get_settings()
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # 1. Create table
            cur.execute(CREATE_TABLE)
            print("✔  app_config table ensured")

            # 2. Seed chat agent asset IDs from .env
            chat_rows = [
                (
                    "chatnow_asset_id",
                    settings.CHATNOW_ASSET_ID or "",
                    "Asset version ID for the guest ChatNow agent",
                ),
                (
                    "intellichat_asset_id",
                    settings.INTELLICHAT_ASSET_ID or "",
                    "Asset version ID for the logged-in IntelliChat agent",
                ),
            ]
            for row in chat_rows:
                cur.execute(UPSERT, row)
            print(f"✔  Seeded {len(chat_rows)} chat agent asset ID rows")

            # 3. Seed subcategory asset IDs from the subcategories table
            cur.execute(
                """
                SELECT c.slug AS cat_slug, s.slug AS sub_slug, s.asset_id, s.name
                FROM subcategories s
                JOIN categories c ON c.id = s.category_id
                WHERE c.is_active = TRUE AND s.is_active = TRUE
                """
            )
            sub_rows = cur.fetchall()
            seeded_subs = 0
            for row in sub_rows:
                # row is a tuple: (cat_slug, sub_slug, asset_id, name)
                cat_slug, sub_slug, asset_id, sub_name = row
                key = f"asset.{cat_slug}.{sub_slug}"
                cur.execute(
                    UPSERT,
                    (key, asset_id or "", f"Asset ID for {sub_name}"),
                )
                seeded_subs += 1
            print(f"✔  Seeded {seeded_subs} subcategory asset ID rows")

        conn.commit()
        print("\n✅  Migration complete. app_config table is ready.")
    except Exception as e:
        conn.rollback()
        print(f"\n❌  Migration failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
