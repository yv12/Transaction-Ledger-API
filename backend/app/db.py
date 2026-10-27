import os
import sqlite3
from contextlib import contextmanager

SCHEMA = """
CREATE TABLE IF NOT EXISTS accounts (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL CHECK (length(trim(name)) > 0),
    balance     INTEGER NOT NULL DEFAULT 0 CHECK (balance >= 0),  -- minor units (cents)
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS transactions (
    id            TEXT PRIMARY KEY,
    account_id    TEXT NOT NULL REFERENCES accounts(id),
    type          TEXT NOT NULL CHECK (type IN ('credit', 'debit')),
    amount        INTEGER NOT NULL CHECK (amount > 0),            -- minor units (cents)
    description   TEXT NOT NULL DEFAULT '',
    reference_id  TEXT NOT NULL CHECK (length(trim(reference_id)) > 0),
    created_at    TEXT NOT NULL,
    UNIQUE (account_id, reference_id)
);

CREATE INDEX IF NOT EXISTS idx_tx_account_created
    ON transactions (account_id, created_at DESC);

-- Transactions are immutable at the database level too.
CREATE TRIGGER IF NOT EXISTS trg_tx_no_update
BEFORE UPDATE ON transactions
BEGIN
    SELECT RAISE(ABORT, 'transactions are immutable');
END;

CREATE TRIGGER IF NOT EXISTS trg_tx_no_delete
BEFORE DELETE ON transactions
BEGIN
    SELECT RAISE(ABORT, 'transactions are immutable');
END;
"""


def init_db(path: str) -> None:
    parent_dir = os.path.dirname(os.path.abspath(path))
    if parent_dir and not os.path.exists(parent_dir):
        os.makedirs(parent_dir, exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


def connect(path: str) -> sqlite3.Connection:
    # isolation_level=None: we control BEGIN/COMMIT ourselves.
    # check_same_thread=False allows FastAPI threadpool workers to safely use request-scoped connections.
    conn = sqlite3.connect(path, check_same_thread=False, isolation_level=None, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def atomic(conn: sqlite3.Connection):
    """One atomic unit of work. BEGIN IMMEDIATE takes the write lock up front,
    so balance checks and updates cannot interleave with another writer."""
    conn.execute("BEGIN IMMEDIATE")
    try:
        yield conn
    except BaseException:
        conn.execute("ROLLBACK")
        raise
    else:
        conn.execute("COMMIT")
