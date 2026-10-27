import math
import sqlite3
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from .db import atomic
from .errors import (
    AccountNotFound,
    DuplicateTransaction,
    InsufficientBalance,
    InvalidTransfer,
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def to_cents(amount: Decimal) -> int:
    return int(amount * 100)


def from_cents(cents: int) -> float:
    return cents / 100


def tx_dict(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "account_id": row["account_id"],
        "type": row["type"],
        "amount": from_cents(row["amount"]),
        "description": row["description"],
        "reference_id": row["reference_id"],
        "created_at": row["created_at"],
    }


def _get_account(conn, account_id: str) -> sqlite3.Row:
    row = conn.execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone()
    if row is None:
        raise AccountNotFound(f"Account '{account_id}' not found")
    return row


def create_account(conn, name: str) -> dict:
    account_id = str(uuid.uuid4())
    created_at = now()
    # Balance is never taken from the client: always starts at 0.
    conn.execute(
        "INSERT INTO accounts (id, name, balance, created_at) VALUES (?, ?, 0, ?)",
        (account_id, name, created_at),
    )
    return {"id": account_id, "name": name, "balance": 0.0, "created_at": created_at}


def list_accounts(conn) -> list[dict]:
    rows = conn.execute("SELECT * FROM accounts ORDER BY created_at DESC").fetchall()
    return [
        {
            "id": r["id"],
            "name": r["name"],
            "balance": from_cents(r["balance"]),
            "created_at": r["created_at"],
        }
        for r in rows
    ]


def get_balance(conn, account_id: str) -> dict:
    acc = _get_account(conn, account_id)
    return {"account_id": acc["id"], "balance": from_cents(acc["balance"])}


def _apply(conn, account_id, tx_type, cents, description, reference_id) -> sqlite3.Row:
    """Insert a transaction and update the balance. Must run inside atomic()."""
    acc = _get_account(conn, account_id)

    existing = conn.execute(
        "SELECT * FROM transactions WHERE account_id = ? AND reference_id = ?",
        (account_id, reference_id),
    ).fetchone()
    if existing:
        raise DuplicateTransaction(
            f"A transaction with reference_id '{reference_id}' already exists for this account",
            tx_dict(existing),
        )

    if tx_type == "debit":
        if acc["balance"] < cents:
            raise InsufficientBalance(
                "Insufficient balance for this debit",
                {"balance": from_cents(acc["balance"]), "requested": from_cents(cents)},
            )
        new_balance = acc["balance"] - cents
    else:
        new_balance = acc["balance"] + cents

    tx_id = str(uuid.uuid4())
    try:
        conn.execute(
            "INSERT INTO transactions (id, account_id, type, amount, description, reference_id, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (tx_id, account_id, tx_type, cents, description, reference_id, now()),
        )
    except sqlite3.IntegrityError:
        # Safety net: the UNIQUE (account_id, reference_id) constraint fired.
        raise DuplicateTransaction(
            f"A transaction with reference_id '{reference_id}' already exists for this account"
        )
    conn.execute("UPDATE accounts SET balance = ? WHERE id = ?", (new_balance, account_id))
    return conn.execute("SELECT * FROM transactions WHERE id = ?", (tx_id,)).fetchone()


def add_transaction(conn, account_id, tx_type, amount, description, reference_id) -> dict:
    with atomic(conn):
        row = _apply(conn, account_id, tx_type, to_cents(amount), description, reference_id)
    return tx_dict(row)


def transfer(conn, from_id, to_id, amount, description, reference_id) -> dict:
    if from_id == to_id:
        raise InvalidTransfer("Source and destination accounts must be different")
    cents = to_cents(amount)
    with atomic(conn):
        _get_account(conn, from_id)
        _get_account(conn, to_id)
        debit = _apply(conn, from_id, "debit", cents, description or f"Transfer to {to_id}", reference_id)
        credit = _apply(conn, to_id, "credit", cents, description or f"Transfer from {from_id}", reference_id)
        from_bal = _get_account(conn, from_id)["balance"]
        to_bal = _get_account(conn, to_id)["balance"]
    return {
        "from_transaction": tx_dict(debit),
        "to_transaction": tx_dict(credit),
        "from_balance": from_cents(from_bal),
        "to_balance": from_cents(to_bal),
    }


def get_history(
    conn,
    account_id,
    tx_type=None,
    page=1,
    limit=10,
    start_date=None,
    end_date=None,
    min_amount=None,
    max_amount=None,
    search=None,
) -> dict:
    _get_account(conn, account_id)
    where = "account_id = ?"
    params: list = [account_id]
    if tx_type:
        where += " AND type = ?"
        params.append(tx_type)
    if start_date:
        where += " AND created_at >= ?"
        params.append(start_date)
    if end_date:
        where += " AND created_at <= ?"
        if len(end_date) == 10:
            params.append(f"{end_date}T23:59:59.999999+00:00")
        else:
            params.append(end_date)
    if min_amount is not None:
        where += " AND amount >= ?"
        params.append(int(Decimal(str(min_amount)) * 100))
    if max_amount is not None:
        where += " AND amount <= ?"
        params.append(int(Decimal(str(max_amount)) * 100))
    if search:
        where += " AND (description LIKE ? OR reference_id LIKE ?)"
        term = f"%{search.strip()}%"
        params.extend([term, term])

    total = conn.execute(f"SELECT COUNT(*) FROM transactions WHERE {where}", params).fetchone()[0]
    rows = conn.execute(
        f"SELECT * FROM transactions WHERE {where}"
        " ORDER BY created_at DESC, rowid DESC LIMIT ? OFFSET ?",
        [*params, limit, (page - 1) * limit],
    ).fetchall()
    return {
        "account_id": account_id,
        "data": [tx_dict(r) for r in rows],
        "pagination": {
            "page": page,
            "limit": limit,
            "total_records": total,
            "total_pages": math.ceil(total / limit) if total else 0,
        },
    }


def get_all_transactions(
    conn,
    tx_type=None,
    page=1,
    limit=10,
    search=None,
) -> dict:
    where = "1=1"
    params: list = []
    if tx_type:
        where += " AND t.type = ?"
        params.append(tx_type)
    if search:
        where += " AND (t.description LIKE ? OR t.reference_id LIKE ? OR a.name LIKE ?)"
        term = f"%{search.strip()}%"
        params.extend([term, term, term])

    count_sql = f"SELECT COUNT(*) FROM transactions t JOIN accounts a ON t.account_id = a.id WHERE {where}"
    total = conn.execute(count_sql, params).fetchone()[0]

    sql = (
        f"SELECT t.*, a.name as account_name FROM transactions t "
        f"JOIN accounts a ON t.account_id = a.id "
        f"WHERE {where} ORDER BY t.created_at DESC, t.rowid DESC LIMIT ? OFFSET ?"
    )
    rows = conn.execute(sql, [*params, limit, (page - 1) * limit]).fetchall()
    return {
        "data": [
            {
                **tx_dict(r),
                "account_name": r["account_name"],
            }
            for r in rows
        ],
        "pagination": {
            "page": page,
            "limit": limit,
            "total_records": total,
            "total_pages": math.ceil(total / limit) if total else 0,
        },
    }


