import sqlite3
import threading

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture()
def db_path(tmp_path):
    return str(tmp_path / "test.db")


@pytest.fixture()
def client(db_path):
    return TestClient(create_app(db_path), raise_server_exceptions=False)


def new_account(client, name="Asha"):
    r = client.post("/accounts", json={"name": name})
    assert r.status_code == 201
    return r.json()["id"]


def tx(client, acc, type_, amount, ref, desc="t"):
    return client.post(
        f"/accounts/{acc}/transactions",
        json={"type": type_, "amount": amount, "reference_id": ref, "description": desc},
    )


def balance(client, acc):
    return client.get(f"/accounts/{acc}/balance").json()["balance"]


# ---- accounts ----
def test_create_account(client):
    r = client.post("/accounts", json={"name": "Asha"})
    body = r.json()
    assert r.status_code == 201
    assert body["balance"] == 0 and body["name"] == "Asha"
    assert body["id"] and body["created_at"]


def test_account_requires_name(client):
    assert client.post("/accounts", json={}).status_code == 422
    assert client.post("/accounts", json={"name": "   "}).status_code == 422


def test_client_cannot_set_balance(client):
    r = client.post("/accounts", json={"name": "A", "balance": 500})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"


def test_invalid_json_body(client):
    r = client.post("/accounts", content="not json", headers={"content-type": "application/json"})
    assert r.status_code == 422


# ---- transactions ----
def test_credit_and_debit(client):
    a = new_account(client)
    assert tx(client, a, "credit", 100, "r1").status_code == 201
    assert balance(client, a) == 100
    assert tx(client, a, "debit", 30, "r2").status_code == 201
    assert balance(client, a) == 70


def test_balance_consistency_example(client):
    a = new_account(client)
    for i, (t, amt) in enumerate([("credit", 100), ("credit", 50), ("debit", 30), ("debit", 20)]):
        assert tx(client, a, t, amt, f"r{i}").status_code == 201
    assert balance(client, a) == 100


def test_insufficient_balance_rejected(client):
    a = new_account(client)
    tx(client, a, "credit", 100, "r1")
    r = tx(client, a, "debit", 150, "r2")
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "INSUFFICIENT_BALANCE"
    assert balance(client, a) == 100
    # rejected transaction is not stored
    assert client.get(f"/accounts/{a}/transactions").json()["pagination"]["total_records"] == 1


def test_duplicate_reference_same_account(client):
    a = new_account(client)
    assert tx(client, a, "credit", 100, "dup").status_code == 201
    r = tx(client, a, "credit", 100, "dup")
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "DUPLICATE_TRANSACTION"
    assert balance(client, a) == 100
    assert client.get(f"/accounts/{a}/transactions").json()["pagination"]["total_records"] == 1


def test_same_reference_different_accounts(client):
    a, b = new_account(client), new_account(client, "Bob")
    assert tx(client, a, "credit", 10, "same").status_code == 201
    assert tx(client, b, "credit", 10, "same").status_code == 201


def test_transaction_validation(client):
    a = new_account(client)
    assert tx(client, a, "refund", 10, "r").status_code == 422
    assert tx(client, a, "credit", 0, "r").status_code == 422
    assert tx(client, a, "credit", -5, "r").status_code == 422
    assert tx(client, a, "credit", "abc", "r").status_code == 422
    assert tx(client, a, "credit", 10.123, "r").status_code == 422
    assert client.post(f"/accounts/{a}/transactions", json={"type": "credit", "amount": 5}).status_code == 422
    assert tx(client, a, "credit", 5, "  ").status_code == 422
    assert balance(client, a) == 0


def test_transaction_unknown_account(client):
    r = tx(client, "nope", "credit", 10, "r")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "ACCOUNT_NOT_FOUND"


def test_decimal_amounts_are_exact(client):
    a = new_account(client)
    for i in range(10):
        tx(client, a, "credit", 0.1, f"r{i}")
    assert balance(client, a) == 1.0


# ---- balance ----
def test_balance_not_found(client):
    r = client.get("/accounts/missing/balance")
    assert r.status_code == 404


# ---- history ----
def test_history_filter_sort_pagination(client):
    a = new_account(client)
    for i in range(5):
        tx(client, a, "credit", 10, f"c{i}")
    for i in range(2):
        tx(client, a, "debit", 1, f"d{i}")

    r = client.get(f"/accounts/{a}/transactions?limit=3&page=1").json()
    assert r["pagination"] == {"page": 1, "limit": 3, "total_records": 7, "total_pages": 3}
    assert [t["reference_id"] for t in r["data"]] == ["d1", "d0", "c4"]  # latest first

    r = client.get(f"/accounts/{a}/transactions?limit=3&page=3").json()
    assert [t["reference_id"] for t in r["data"]] == ["c0"]

    r = client.get(f"/accounts/{a}/transactions?type=debit").json()
    assert r["pagination"]["total_records"] == 2
    assert all(t["type"] == "debit" for t in r["data"])

    r = client.get(f"/accounts/{a}/transactions?type=credit").json()
    assert r["pagination"]["total_records"] == 5


def test_history_invalid_params(client):
    a = new_account(client)
    for q in ["page=0", "limit=0", "limit=101", "page=abc", "type=refund"]:
        r = client.get(f"/accounts/{a}/transactions?{q}")
        assert r.status_code == 422, q
        assert r.json()["error"]["code"] == "VALIDATION_ERROR"


def test_history_unknown_account(client):
    assert client.get("/accounts/missing/transactions").status_code == 404


def test_empty_history(client):
    a = new_account(client)
    r = client.get(f"/accounts/{a}/transactions").json()
    assert r["data"] == [] and r["pagination"]["total_pages"] == 0


# ---- immutability ----
def test_transactions_cannot_be_changed_via_api(client):
    a = new_account(client)
    t = tx(client, a, "credit", 10, "r").json()
    for method in ("put", "patch", "delete"):
        r = getattr(client, method)(f"/accounts/{a}/transactions/{t['id']}")
        assert r.status_code == 405


def test_database_blocks_update_and_delete(client, db_path):
    a = new_account(client)
    tx(client, a, "credit", 10, "r")
    conn = sqlite3.connect(db_path)
    with pytest.raises(sqlite3.DatabaseError):
        conn.execute("UPDATE transactions SET amount = 999")
    with pytest.raises(sqlite3.DatabaseError):
        conn.execute("DELETE FROM transactions")
    conn.close()


def test_database_blocks_negative_balance(client, db_path):
    a = new_account(client)
    conn = sqlite3.connect(db_path)
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("UPDATE accounts SET balance = -1 WHERE id = ?", (a,))
    conn.close()


# ---- atomicity ----
def test_failure_midway_rolls_back(client, db_path, monkeypatch):
    """If the balance update fails after the transaction insert, nothing persists."""
    a = new_account(client)
    conn = sqlite3.connect(db_path)
    # Force the UPDATE on accounts to fail.
    conn.execute(
        "CREATE TRIGGER boom BEFORE UPDATE ON accounts BEGIN SELECT RAISE(ABORT, 'boom'); END"
    )
    conn.commit()
    conn.close()

    r = tx(client, a, "credit", 50, "r1")
    assert r.status_code == 500
    conn = sqlite3.connect(db_path)
    conn.execute("DROP TRIGGER boom")
    conn.commit()
    conn.close()

    assert balance(client, a) == 0
    assert client.get(f"/accounts/{a}/transactions").json()["pagination"]["total_records"] == 0


def test_concurrent_debits_never_overdraw(client, db_path):
    a = new_account(client)
    tx(client, a, "credit", 100, "seed")
    results = []

    def worker(i):
        c = TestClient(create_app(db_path))
        results.append(tx(c, a, "debit", 30, f"d{i}").status_code)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
    [t.start() for t in threads]
    [t.join() for t in threads]

    assert results.count(201) == 3
    assert balance(client, a) == 10


def test_concurrent_duplicate_reference(client, db_path):
    a = new_account(client)
    results = []

    def worker():
        c = TestClient(create_app(db_path))
        results.append(tx(c, a, "credit", 10, "same").status_code)

    threads = [threading.Thread(target=worker) for _ in range(6)]
    [t.start() for t in threads]
    [t.join() for t in threads]

    assert results.count(201) == 1 and results.count(409) == 5
    assert balance(client, a) == 10


# ---- transfer (bonus) ----
def test_transfer_success(client):
    a, b = new_account(client), new_account(client, "Bob")
    tx(client, a, "credit", 100, "s1")
    tx(client, b, "credit", 50, "s2")
    r = client.post("/transfers", json={"from_account_id": a, "to_account_id": b, "amount": 30, "reference_id": "t1"})
    assert r.status_code == 201
    assert balance(client, a) == 70
    assert balance(client, b) == 80
    body = r.json()
    assert body["from_transaction"]["type"] == "debit"
    assert body["to_transaction"]["type"] == "credit"


def test_transfer_insufficient_rolls_back(client):
    a, b = new_account(client), new_account(client, "Bob")
    tx(client, a, "credit", 10, "s1")
    r = client.post("/transfers", json={"from_account_id": a, "to_account_id": b, "amount": 30, "reference_id": "t1"})
    assert r.status_code == 422
    assert balance(client, a) == 10 and balance(client, b) == 0


def test_transfer_missing_account_rolls_back(client):
    a = new_account(client)
    tx(client, a, "credit", 100, "s1")
    r = client.post("/transfers", json={"from_account_id": a, "to_account_id": "ghost", "amount": 30, "reference_id": "t1"})
    assert r.status_code == 404
    assert balance(client, a) == 100


def test_transfer_to_self_rejected(client):
    a = new_account(client)
    tx(client, a, "credit", 100, "s1")
    r = client.post("/transfers", json={"from_account_id": a, "to_account_id": a, "amount": 10, "reference_id": "t1"})
    assert r.status_code == 422
    assert balance(client, a) == 100


def test_transfer_duplicate_reference_is_not_applied_twice(client):
    a, b = new_account(client), new_account(client, "Bob")
    tx(client, a, "credit", 100, "s1")
    body = {"from_account_id": a, "to_account_id": b, "amount": 30, "reference_id": "t1"}
    assert client.post("/transfers", json=body).status_code == 201
    assert client.post("/transfers", json=body).status_code == 409
    assert balance(client, a) == 70 and balance(client, b) == 30


def test_transfer_partial_failure_rolls_back_debit(client):
    """Destination already used this reference_id: the debit on source must roll back."""
    a, b = new_account(client), new_account(client, "Bob")
    tx(client, a, "credit", 100, "s1")
    tx(client, b, "credit", 5, "t1")  # b already has reference t1
    r = client.post("/transfers", json={"from_account_id": a, "to_account_id": b, "amount": 30, "reference_id": "t1"})
    assert r.status_code == 409
    assert balance(client, a) == 100 and balance(client, b) == 5


def test_all_transactions_latest_first(client):
    a = new_account(client, "Alice")
    b = new_account(client, "Bob")
    tx(client, a, "credit", 100, "ref-1")
    tx(client, b, "credit", 200, "ref-2")
    tx(client, a, "debit", 30, "ref-3")

    r = client.get("/transactions")
    assert r.status_code == 200
    data = r.json()["data"]
    assert len(data) == 3
    # Latest first: ref-3, then ref-2, then ref-1
    assert data[0]["reference_id"] == "ref-3"
    assert data[1]["reference_id"] == "ref-2"
    assert data[2]["reference_id"] == "ref-1"
    assert data[0]["account_name"] == "Alice"
    assert data[1]["account_name"] == "Bob"

