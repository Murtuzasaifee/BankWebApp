"""
Migration script — creates the app_config table and seeds all asset IDs.

Seeds:
  - chatnow       — Asset version ID for the guest ChatNow agent
  - intellichat   — Asset version ID for the logged-in IntelliChat agent
  - <sub_slug>    — one row per subcategory (hyphens → underscores)
                    e.g. savings_account, personal_loan, demat_account

Key naming: simple single-word keys (no dots, no category prefix).

Safe to run multiple times (uses ON CONFLICT DO UPDATE).

Run standalone:
    python scripts/migrate_add_app_config.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.connection import get_connection

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
    value       = EXCLUDED.value,
    description = EXCLUDED.description,
    updated_at  = NOW();
"""


def migrate():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # 1. Create table
            cur.execute(CREATE_TABLE)
            print("✔  app_config table ensured")

            # 2. Seed chat agent rows (values left blank — admin sets them via UI)
            chat_rows = [
                ("chatnow",      "", "Asset version ID for the guest ChatNow agent"),
                ("intellichat",  "", "Asset version ID for the logged-in IntelliChat agent"),
            ]
            for row in chat_rows:
                cur.execute(UPSERT, row)
            print(f"✔  Seeded {len(chat_rows)} chat agent rows (values blank — set via Admin UI)")

            # 3. Seed subcategory rows from the subcategories table
            #    Key = sub_slug with hyphens replaced by underscores
            cur.execute(
                """
                SELECT s.slug AS sub_slug, s.name AS sub_name
                FROM subcategories s
                JOIN categories c ON c.id = s.category_id
                WHERE c.is_active = TRUE AND s.is_active = TRUE
                """
            )
            sub_rows = cur.fetchall()
            seeded_subs = 0
            for row in sub_rows:
                sub_slug, sub_name = row
                key = sub_slug.replace("-", "_")
                cur.execute(UPSERT, (key, "", f"Asset ID for {sub_name}"))
                seeded_subs += 1
            print(f"✔  Seeded {seeded_subs} subcategory rows (values blank — set via Admin UI)")

            # 4. Drop the now-unused asset_id column from subcategories (idempotent)
            cur.execute(
                """
                ALTER TABLE subcategories
                    DROP COLUMN IF EXISTS asset_id;
                """
            )
            print("✔  Dropped asset_id column from subcategories (if it existed)")

        conn.commit()
        print("\n✅  Migration complete. Set asset IDs via the Admin UI → Asset Configuration.")
    except Exception as e:
        conn.rollback()
        print(f"\n❌  Migration failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
