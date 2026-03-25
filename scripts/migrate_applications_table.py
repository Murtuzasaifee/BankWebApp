"""
Migration script — replaces request_logs with the applications table.

Steps:
  1. Create the applications table and indexes (idempotent).
  2. Migrate existing request_logs rows, assigning friendly IDs.
  3. Verify row counts.
  4. Rename request_logs -> request_logs_archived (safety net).

Run standalone:
    python scripts/migrate_applications_table.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.connection import get_connection

# ---------------------------------------------------------------------------
# DDL
# ---------------------------------------------------------------------------

CREATE_APPLICATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS applications (
    id              SERIAL PRIMARY KEY,
    application_id  VARCHAR(20) UNIQUE NOT NULL,
    trace_id        VARCHAR(100) NOT NULL,
    user_id         VARCHAR(20),
    username        VARCHAR(100),
    display_name    VARCHAR(100),
    service_type    VARCHAR(30) NOT NULL,
    service_name    VARCHAR(100) NOT NULL,
    status          VARCHAR(30) NOT NULL DEFAULT 'Submitted',
    admin_comments  TEXT,
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);
"""

CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_applications_user_id    ON applications(user_id);",
    "CREATE INDEX IF NOT EXISTS idx_applications_status     ON applications(status);",
    "CREATE INDEX IF NOT EXISTS idx_applications_created_at ON applications(created_at DESC);",
]

# Migrate from request_logs using window-function row numbers for friendly IDs
MIGRATE_DATA = """
INSERT INTO applications (
    application_id, trace_id, user_id, service_type, service_name,
    status, created_at, updated_at
)
SELECT
    CASE request_type
        WHEN 'loan-application' THEN
            'LOAN-' || LPAD(
                ROW_NUMBER() OVER (PARTITION BY request_type ORDER BY id)::text,
                6, '0'
            )
        WHEN 'savings-account' THEN
            'SAV-' || LPAD(
                ROW_NUMBER() OVER (PARTITION BY request_type ORDER BY id)::text,
                6, '0'
            )
        WHEN 'stock-account' THEN
            'STK-' || LPAD(
                ROW_NUMBER() OVER (PARTITION BY request_type ORDER BY id)::text,
                6, '0'
            )
        ELSE
            'APP-' || LPAD(
                ROW_NUMBER() OVER (PARTITION BY request_type ORDER BY id)::text,
                6, '0'
            )
    END AS application_id,
    COALESCE(trace_id, 'UNKNOWN-' || id::text) AS trace_id,
    user_id,
    CASE request_type
        WHEN 'loan-application' THEN 'loan'
        WHEN 'savings-account'  THEN 'savings'
        WHEN 'stock-account'    THEN 'stock'
        ELSE request_type
    END AS service_type,
    CASE request_type
        WHEN 'loan-application' THEN COALESCE(account_type, 'Loan Application')
        WHEN 'savings-account'  THEN 'Savings Account'
        WHEN 'stock-account'    THEN 'Demat Account'
        ELSE COALESCE(account_type, request_type)
    END AS service_name,
    COALESCE(status, 'In Progress') AS status,
    created_at,
    created_at
FROM request_logs
ON CONFLICT (application_id) DO NOTHING;
"""


def _table_exists(cur, table_name: str) -> bool:
    cur.execute(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = %s)",
        (table_name,),
    )
    return cur.fetchone()[0]


def run():
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Step 1 — create applications table
            print("Step 1: Creating applications table...")
            cur.execute(CREATE_APPLICATIONS_TABLE)
            for idx_sql in CREATE_INDEXES:
                cur.execute(idx_sql)
            print("  applications table and indexes ready.")

            # Step 2 — migrate data (only if request_logs exists)
            source_exists = _table_exists(cur, "request_logs")
            source_count = 0
            migrated = 0

            if source_exists:
                print("Step 2: Migrating rows from request_logs...")
                cur.execute("SELECT COUNT(*) FROM request_logs")
                source_count = cur.fetchone()[0]
                print(f"  Found {source_count} rows in request_logs.")

                if source_count > 0:
                    cur.execute(MIGRATE_DATA)
                    migrated = cur.rowcount
                    print(f"  Migrated {migrated} rows into applications.")
                    if migrated < source_count:
                        print(f"  WARNING: {source_count - migrated} rows skipped (likely duplicate application_id).")
                else:
                    print("  No rows to migrate.")
            else:
                print("Step 2: request_logs table not found — skipping migration.")

            # Step 3 — verify
            cur.execute("SELECT COUNT(*) FROM applications")
            app_count = cur.fetchone()[0]
            print(f"Step 3: applications table now has {app_count} rows.")

            # Step 4 — rename request_logs
            if source_exists:
                archived_exists = _table_exists(cur, "request_logs_archived")
                if archived_exists:
                    print("Step 4: request_logs_archived already exists — skipping rename.")
                else:
                    print("Step 4: Renaming request_logs -> request_logs_archived...")
                    cur.execute("ALTER TABLE request_logs RENAME TO request_logs_archived")
                    print("  Done. request_logs_archived preserved for 30-day safety window.")
            else:
                print("Step 4: No request_logs to rename.")

            conn.commit()
            print("\nMigration complete.")


if __name__ == "__main__":
    run()
