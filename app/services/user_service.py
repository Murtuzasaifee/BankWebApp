"""
User service layer — all DB access for user data goes through here.
"""

from decimal import Decimal

from app.db.connection import execute_query


def _to_float(val):
    """Convert Decimal to float for JSON serialization."""
    return float(val) if isinstance(val, Decimal) else val


def _build_user_dict(user_row, accounts_rows, txn_rows):
    """Assemble a user_data dict matching the shape the frontend expects."""
    data = dict(user_row)
    # Strip internal / sensitive fields
    data.pop("id", None)
    data.pop("created_at", None)
    data.pop("password", None)
    # Convert Decimals
    data["monthly_salary"] = _to_float(data.get("monthly_salary"))

    data["accounts"] = [
        {
            "type": a["type"],
            "balance": _to_float(a["balance"]),
            "number": a["number"],
        }
        for a in accounts_rows
    ]
    data["transactions"] = [
        {
            "id": t["txn_id"],
            "merchant": t["merchant"],
            "date": t["date"],
            "time": t["time"],
            "type": t["type"],
            "amount": _to_float(t["amount"]),
            "status": t["status"],
            "icon": t["icon"],
        }
        for t in txn_rows
    ]
    return data


def get_user_by_credentials(username: str, password: str):
    """
    Authenticate a user by username + password.

    Returns the full user_data dict (no password) or None.
    """
    rows = execute_query(
        "SELECT * FROM users WHERE username = %s AND password = %s",
        (username, password),
    )
    if not rows:
        return None

    user_row = rows[0]
    user_id = user_row["user_id"]

    accounts = execute_query(
        "SELECT type, balance, number FROM accounts WHERE user_id = %s",
        (user_id,),
    )
    transactions = execute_query(
        "SELECT txn_id, merchant, date, time, type, amount, status, icon FROM transactions WHERE user_id = %s",
        (user_id,),
    )
    return _build_user_dict(user_row, accounts, transactions)


def get_user_profile(user_id: str):
    """
    Fetch a user profile by user_id.

    Returns the full user_data dict (no password) or None.
    """
    rows = execute_query(
        "SELECT * FROM users WHERE user_id = %s",
        (user_id,),
    )
    if not rows:
        return None

    user_row = rows[0]

    accounts = execute_query(
        "SELECT type, balance, number FROM accounts WHERE user_id = %s",
        (user_id,),
    )
    transactions = execute_query(
        "SELECT txn_id, merchant, date, time, type, amount, status, icon FROM transactions WHERE user_id = %s",
        (user_id,),
    )
    return _build_user_dict(user_row, accounts, transactions)
