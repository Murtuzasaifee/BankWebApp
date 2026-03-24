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

    # Build payment_instruments from accounts rows
    data["payment_instruments"] = []
    for a in accounts_rows:
        limits = {}
        if a.get("per_txn_limit") is not None:
            limits["per_transaction_limit"] = _to_float(a["per_txn_limit"])
        if a.get("daily_limit") is not None:
            limits["daily_transaction_limit"] = _to_float(a["daily_limit"])
        if a.get("monthly_limit") is not None:
            limits["monthly_transaction_limit"] = _to_float(a["monthly_limit"])
        if a.get("available_credit") is not None:
            limits["available_credit"] = _to_float(a["available_credit"])

        data["payment_instruments"].append({
            "instrument_type": a.get("instrument_type"),
            "instrument_id": a.get("instrument_id"),
            "account_number": a.get("account_number"),
            "account_type": a.get("account_type"),
            "account_status": a.get("account_status"),
            "branch_code": a.get("branch_code"),
            "currency": a.get("currency"),
            "status": a.get("account_status", "Active"),
            "balance": _to_float(a.get("balance")),
            "limits": limits,
        })

    # Keep the simple accounts list for the dashboard UI
    data["accounts"] = [
        {
            "type": a["type"],
            "balance": _to_float(a["balance"]),
            "number": a["account_number"],
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
        "SELECT type, balance, account_number, account_type, account_status, branch_code, currency, "
        "instrument_type, instrument_id, per_txn_limit, daily_limit, monthly_limit, available_credit "
        "FROM accounts WHERE user_id = %s",
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
        "SELECT type, balance, account_number, account_type, account_status, branch_code, currency, "
        "instrument_type, instrument_id, per_txn_limit, daily_limit, monthly_limit, available_credit "
        "FROM accounts WHERE user_id = %s",
        (user_id,),
    )
    transactions = execute_query(
        "SELECT txn_id, merchant, date, time, type, amount, status, icon FROM transactions WHERE user_id = %s",
        (user_id,),
    )
    return _build_user_dict(user_row, accounts, transactions)
