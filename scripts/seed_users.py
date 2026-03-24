"""
Seed script: creates users, accounts, transactions tables and inserts demo data.

Usage:
    python scripts/seed_users.py
"""

import os
import sys

# Allow running from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db.connection import get_connection
from scripts.demo_data import USERS


SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "..", "app", "db", "schema.sql")


def run_schema(conn):
    """Execute schema.sql to create all 3 tables."""
    with open(SCHEMA_PATH) as f:
        ddl = f.read()
    with conn.cursor() as cur:
        cur.execute(ddl)
    conn.commit()
    print("Schema applied successfully (3 tables).")


def seed_users(conn):
    """Upsert demo users and their accounts/transactions."""
    upsert_user_sql = """
        INSERT INTO users (
            user_id, username, password, display_name,
            country_code, account_number, employer, designation,
            monthly_salary, mobile, address
        ) VALUES (
            %(user_id)s, %(username)s, %(password)s, %(display_name)s,
            %(country_code)s, %(account_number)s, %(employer)s, %(designation)s,
            %(monthly_salary)s, %(mobile)s, %(address)s
        )
        ON CONFLICT (username) DO UPDATE SET
            password = EXCLUDED.password,
            display_name = EXCLUDED.display_name,
            country_code = EXCLUDED.country_code,
            account_number = EXCLUDED.account_number,
            employer = EXCLUDED.employer,
            designation = EXCLUDED.designation,
            monthly_salary = EXCLUDED.monthly_salary,
            mobile = EXCLUDED.mobile,
            address = EXCLUDED.address;
    """

    insert_account_sql = """
        INSERT INTO accounts (user_id, type, balance, number)
        VALUES (%(user_id)s, %(type)s, %(balance)s, %(number)s);
    """

    insert_txn_sql = """
        INSERT INTO transactions (user_id, txn_id, merchant, date, time, type, amount, status, icon)
        VALUES (%(user_id)s, %(txn_id)s, %(merchant)s, %(date)s, %(time)s, %(type)s, %(amount)s, %(status)s, %(icon)s);
    """

    with conn.cursor() as cur:
        for username, data in USERS.items():
            user_id = data.get("user_id")

            # Upsert user
            cur.execute(upsert_user_sql, {
                "user_id": user_id,
                "username": username,
                "password": data.get("password"),
                "display_name": data.get("display_name", username),
                "country_code": data.get("country_code"),
                "account_number": data.get("account_number"),
                "employer": data.get("employer"),
                "designation": data.get("designation"),
                "monthly_salary": data.get("monthly_salary"),
                "mobile": data.get("mobile"),
                "address": data.get("address"),
            })
            print(f"  Upserted user: {username}")

            # Clean re-seed: delete existing accounts/transactions for this user
            cur.execute("DELETE FROM accounts WHERE user_id = %s", (user_id,))
            cur.execute("DELETE FROM transactions WHERE user_id = %s", (user_id,))

            # Insert accounts
            for acct in data.get("accounts", []):
                cur.execute(insert_account_sql, {
                    "user_id": user_id,
                    "type": acct["type"],
                    "balance": acct["balance"],
                    "number": acct["number"],
                })
            print(f"    Inserted {len(data.get('accounts', []))} accounts")

            # Insert transactions
            for txn in data.get("transactions", []):
                cur.execute(insert_txn_sql, {
                    "user_id": user_id,
                    "txn_id": txn["id"],
                    "merchant": txn["merchant"],
                    "date": txn["date"],
                    "time": txn["time"],
                    "type": txn["type"],
                    "amount": txn["amount"],
                    "status": txn["status"],
                    "icon": txn["icon"],
                })
            print(f"    Inserted {len(data.get('transactions', []))} transactions")

    conn.commit()
    print(f"\nSeeded {len(USERS)} users with accounts & transactions.")


if __name__ == "__main__":
    conn = get_connection()
    try:
        run_schema(conn)
        seed_users(conn)
    finally:
        conn.close()
    print("Done.")
