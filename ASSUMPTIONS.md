# 📝 System Design & Architectural Assumptions

This document outlines the core business, financial, architectural, and data integrity assumptions made during the design and implementation of the **Aether Transaction Ledger System**.

---

## 1. Monetary Precision & Representation

### Assumption: Integer Minor Units (Cents)
- **Rationale:** Financial systems cannot tolerate floating-point rounding errors (e.g., `0.1 + 0.2 = 0.30000000000000004` under IEEE 754). 
- **Implementation:** 
  - All monetary values are validated via Pydantic v2 to have at most 2 decimal places.
  - Internally, all values are quantized and persisted in the database as **integer cents** (`$10.50` is stored as `1050`).
  - Balance calculations and comparisons are strictly integer arithmetic.
  - Values are converted back to exact 2-decimal floats (`amount / 100`) strictly at the API response serialization boundary.

---

## 2. Currency Model

### Assumption: Single Domestic Currency
- **Rationale:** To maintain absolute ACID guarantees and eliminate external network failure vectors (such as third-party FX rate API outages), the system operates on a single domestic fiat currency unit.
- **Future Extension:** Multi-currency support can be implemented by adding a `currency` column to `accounts` and introducing an FX conversion quote ledger prior to executing transfers.

---

## 3. Ledger Immutability & Audit Integrity

### Assumption: Strict Append-Only Journal
- **Rationale:** In standard accounting principles, historical financial records must never be modified or deleted. Any corrections or reversals must be recorded as explicit offsetting entries.
- **Defense in Depth:**
  1. **API Layer:** No `PUT`, `PATCH`, or `DELETE` endpoints exist for transactions. Any attempted request to `/accounts/{id}/transactions/{tx_id}` returns `405 Method Not Allowed` with code `TRANSACTION_IMMUTABLE`.
  2. **Database Layer (Triggers):** SQLite triggers `trg_tx_no_update` and `trg_tx_no_delete` abort any direct SQL `UPDATE` or `DELETE` statements on the `transactions` table.
  3. **Non-Negative Balance Constraint:** The `accounts` table enforces `CHECK (balance >= 0)` at the SQLite engine level.

---

## 4. Concurrency & Atomicity Guarantees

### Assumption: Immediate Write Locking (`BEGIN IMMEDIATE`)
- **Rationale:** In high-concurrency environments, checking an account balance and subsequently deducting funds across separate read/write queries introduces a **time-of-check to time-of-use (TOCTOU)** double-spend vulnerability.
- **Implementation:**
  - Every transaction and transfer is wrapped in an atomic context manager executing `BEGIN IMMEDIATE`.
  - SQLite reserves an exclusive write lock *before* reading the account balance.
  - Concurrent debit requests are serialized, preventing overdraws even when multiple requests arrive in parallel (verified with multithreaded pytest suite).

---

## 5. Idempotency & Duplicate Request Protection

### Assumption: Reference IDs are Unique per Account
- **Rationale:** Network timeouts or client retries can lead to duplicate charges if transactions are not idempotent.
- **Implementation:**
  - Every transaction requires a client-provided `reference_id` (e.g. invoice number, payment gateway charge ID).
  - A compound unique database constraint `UNIQUE (account_id, reference_id)` guarantees that no transaction is executed twice.
  - Duplicate requests are rejected with `409 Conflict` (`DUPLICATE_TRANSACTION`).
  - The same `reference_id` can be used across different accounts, allowing cross-system reconciliation.

---

## 6. Account Lifecycle & Initial Balances

### Assumption: Accounts Start at Zero Balance
- **Rationale:** Money cannot materialize out of thin air. An account balance should only increase via an auditable, recorded credit transaction.
- **Implementation:**
  - The `POST /accounts` endpoint strictly initializes `balance = 0`.
  - Any attempt by the client to inject an initial balance payload is rejected with `422 Unprocessable Entity` via Pydantic's `extra="forbid"`.

---

## 7. Inter-Account Transfers

### Assumption: Dual-Leg Single Atomic Transaction
- **Rationale:** A fund transfer consists of a debit from Account A and a credit to Account B. If either leg fails, the entire operation must be aborted to prevent funds from vanishing or duplicating.
- **Implementation:**
  - Both ledger entries are executed inside a single `BEGIN IMMEDIATE` transaction block.
  - Transfers to self (`from_account_id == to_account_id`) are rejected with `422`.
  - If the destination account does not exist or has already used the reference ID, the source account debit is automatically rolled back.

---

## 8. Identifiers & Timestamps

- **Identifiers:** Primary keys for accounts and transactions are generated server-side as globally unique **UUIDv4** strings.
- **Timestamps:** All transaction timestamps are generated in UTC following the **ISO 8601** standard (`YYYY-MM-DDTHH:MM:SS.ffffff+00:00`).

---

## 9. Deployment & Persistence

- **Containerization:** A multi-stage Docker build compiles the Vite frontend and packages it with the Python/FastAPI backend into a single runnable container.
- **Railway Persistence:** SQLite data is stored either in `./ledger.db` or automatically in `/data/ledger.db` when a persistent volume is mounted in Railway.
