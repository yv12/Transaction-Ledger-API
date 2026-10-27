# 📖 Transaction Ledger API — Technical Specification

A complete, high-integrity REST API reference for the **Aether Transaction Ledger System**.

---

## 🌐 Base URLs & Interactive Documentation

| Environment | Base URL | Interactive Swagger UI | ReDoc Specification |
| :--- | :--- | :--- | :--- |
| **Local Development** | `http://127.0.0.1:8000` | [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) | [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc) |
| **Production (Railway)** | `https://<your-app>.up.railway.app` | `https://<your-app>.up.railway.app/docs` | `https://<your-app>.up.railway.app/redoc` |
| **OpenAPI 3.1 Spec** | `/openapi.json` | Import directly into Postman, Insomnia, or Swagger Editor | |

---

## 🛡️ Standardized Error Contract

All non-2xx responses adhere to a consistent, machine-readable JSON structure:

```json
{
  "error": {
    "code": "INSUFFICIENT_BALANCE",
    "message": "Account balance (100.00) is insufficient for debit of 150.00",
    "details": null
  }
}
```

### Standard Error Codes

| Status Code | Error Code | Description |
| :--- | :--- | :--- |
| `400` | `BAD_REQUEST` | Malformed request syntax or parameters |
| `404` | `ACCOUNT_NOT_FOUND` | Specified account does not exist |
| `405` | `TRANSACTION_IMMUTABLE` | Transactions are immutable; modifications and deletions are prohibited |
| `409` | `DUPLICATE_TRANSACTION` | The `reference_id` has already been recorded for this account |
| `422` | `INSUFFICIENT_BALANCE` | Debit amount exceeds the available account balance |
| `422` | `VALIDATION_ERROR` | Schema validation error (invalid decimal places, missing name, negative amount) |
| `500` | `INTERNAL_SERVER_ERROR` | Server-side execution exception; database automatically rolled back |

---

## 📌 Endpoint Reference

### 1. Create Account
Creates a new ledger account. Balance strictly initializes to `0.0`.

- **Method & Route:** `POST /accounts`
- **Headers:** `Content-Type: application/json`
- **Request Body:**
  ```json
  {
    "name": "Jane Doe"
  }
  ```
- **Validation Rules:**
  - `name`: Required, non-empty, 1–100 characters (whitespace trimmed).
  - Client cannot specify an initial balance (`extra="forbid"` returns `422`).
- **Response (`201 Created`):**
  ```json
  {
    "id": "7f0c18d4-5ea7-4b19-b7b5-23c5cf8c39e2",
    "name": "Jane Doe",
    "balance": 0.0,
    "created_at": "2026-10-28T01:00:00.123456+00:00"
  }
  ```
- **cURL Example:**
  ```bash
  curl -X POST "http://127.0.0.1:8000/accounts" \
    -H "Content-Type: application/json" \
    -d '{"name": "Jane Doe"}'
  ```

---

### 2. List All Accounts
Returns a list of all active ledger accounts, sorted alphabetically.

- **Method & Route:** `GET /accounts`
- **Response (`200 OK`):**
  ```json
  [
    {
      "id": "7f0c18d4-5ea7-4b19-b7b5-23c5cf8c39e2",
      "name": "Jane Doe",
      "balance": 150.0,
      "created_at": "2026-10-28T01:00:00.123456+00:00"
    }
  ]
  ```
- **cURL Example:**
  ```bash
  curl -X GET "http://127.0.0.1:8000/accounts"
  ```

---

### 3. Add Transaction (Credit / Debit)
Posts an immutable credit or debit to the target account. Executes within an atomic write lock (`BEGIN IMMEDIATE`).

- **Method & Route:** `POST /accounts/{account_id}/transactions`
- **Request Body:**
  ```json
  {
    "type": "credit",
    "amount": 250.75,
    "description": "Invoice payment #104",
    "reference_id": "INV-2026-001"
  }
  ```
- **Validation Rules:**
  - `type`: Must be strictly `"credit"` or `"debit"`.
  - `amount`: Number strictly greater than `0`, with at most 2 decimal places.
  - `reference_id`: Required string (1–100 chars). Must be unique per account.
  - For `debit`: Rejects with `422 INSUFFICIENT_BALANCE` if `balance < amount`.
- **Response (`201 Created`):**
  ```json
  {
    "id": "c138fd90-9556-4b8a-9fbc-891d2938a1ef",
    "account_id": "7f0c18d4-5ea7-4b19-b7b5-23c5cf8c39e2",
    "type": "credit",
    "amount": 250.75,
    "description": "Invoice payment #104",
    "reference_id": "INV-2026-001",
    "created_at": "2026-10-28T01:05:00.654321+00:00"
  }
  ```
- **cURL Example:**
  ```bash
  curl -X POST "http://127.0.0.1:8000/accounts/7f0c18d4-5ea7-4b19-b7b5-23c5cf8c39e2/transactions" \
    -H "Content-Type: application/json" \
    -d '{
      "type": "credit",
      "amount": 250.75,
      "description": "Invoice payment #104",
      "reference_id": "INV-2026-001"
    }'
  ```

---

### 4. Get Account Balance
Retrieves the real-time available balance for an account.

- **Method & Route:** `GET /accounts/{account_id}/balance`
- **Response (`200 OK`):**
  ```json
  {
    "account_id": "7f0c18d4-5ea7-4b19-b7b5-23c5cf8c39e2",
    "balance": 250.75
  }
  ```
- **Error Response (`404 Not Found`):** If account ID does not exist.
- **cURL Example:**
  ```bash
  curl -X GET "http://127.0.0.1:8000/accounts/7f0c18d4-5ea7-4b19-b7b5-23c5cf8c39e2/balance"
  ```

---

### 5. Get Transaction History
Retrieves paginated, filtered transaction history for an account, sorted latest-first (`created_at DESC`).

- **Method & Route:** `GET /accounts/{account_id}/transactions`
- **Query Parameters:**
  | Parameter | Type | Default | Description |
  | :--- | :--- | :--- | :--- |
  | `type` | String | `null` | Filter by `"credit"` or `"debit"`. Omit to return both. |
  | `page` | Integer | `1` | Page number (must be `>= 1`). |
  | `limit` | Integer | `10` | Records per page (range: `1` to `100`). |
  | `start_date`| String | `null` | Filter from date (`YYYY-MM-DD` or ISO 8601). |
  | `end_date` | String | `null` | Filter up to date (`YYYY-MM-DD` or ISO 8601). |
  | `min_amount`| Float | `null` | Filter by minimum transaction amount. |
  | `max_amount`| Float | `null` | Filter by maximum transaction amount. |
  | `search` | String | `null` | Substring search across description and reference ID. |
- **Response (`200 OK`):**
  ```json
  {
    "account_id": "7f0c18d4-5ea7-4b19-b7b5-23c5cf8c39e2",
    "data": [
      {
        "id": "c138fd90-9556-4b8a-9fbc-891d2938a1ef",
        "account_id": "7f0c18d4-5ea7-4b19-b7b5-23c5cf8c39e2",
        "type": "credit",
        "amount": 250.75,
        "description": "Invoice payment #104",
        "reference_id": "INV-2026-001",
        "created_at": "2026-10-28T01:05:00.654321+00:00"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 10,
      "total_records": 1,
      "total_pages": 1
    }
  }
  ```
- **cURL Example:**
  ```bash
  curl -X GET "http://127.0.0.1:8000/accounts/7f0c18d4-5ea7-4b19-b7b5-23c5cf8c39e2/transactions?limit=10&page=1&type=credit"
  ```

---

### 6. Atomic Peer-to-Peer Transfer (Bonus Feature)
Atomically debits funds from the source account and credits them to the destination account in a single atomic transaction.

- **Method & Route:** `POST /transfers`
- **Request Body:**
  ```json
  {
    "from_account_id": "7f0c18d4-5ea7-4b19-b7b5-23c5cf8c39e2",
    "to_account_id": "3e9b11a2-4dd6-4f71-a0c3-11f8e2345b90",
    "amount": 50.00,
    "description": "Monthly subscription share",
    "reference_id": "XFER-9902"
  }
  ```
- **Guarantees & Invariants:**
  - `from_account_id` cannot equal `to_account_id` (`422`).
  - Single database transaction lock (`BEGIN IMMEDIATE`).
  - If source account has insufficient funds, nothing is posted (`422`).
  - If destination fails (e.g. duplicate reference or invalid account), source debit is completely rolled back.
- **Response (`201 Created`):**
  ```json
  {
    "from_transaction": {
      "id": "e21908...",
      "account_id": "7f0c18d4...",
      "type": "debit",
      "amount": 50.0,
      "description": "Monthly subscription share",
      "reference_id": "XFER-9902",
      "created_at": "2026-10-28T01:10:00.000000+00:00"
    },
    "to_transaction": {
      "id": "90af23...",
      "account_id": "3e9b11a2...",
      "type": "credit",
      "amount": 50.0,
      "description": "Monthly subscription share",
      "reference_id": "XFER-9902",
      "created_at": "2026-10-28T01:10:00.000000+00:00"
    },
    "from_balance": 200.75,
    "to_balance": 50.0
  }
  ```
- **cURL Example:**
  ```bash
  curl -X POST "http://127.0.0.1:8000/transfers" \
    -H "Content-Type: application/json" \
    -d '{
      "from_account_id": "7f0c18d4-5ea7-4b19-b7b5-23c5cf8c39e2",
      "to_account_id": "3e9b11a2-4dd6-4f71-a0c3-11f8e2345b90",
      "amount": 50.00,
      "description": "Monthly subscription share",
      "reference_id": "XFER-9902"
    }'
  ```

---

### 7. Global Transaction Audit Journal (Admin)
Returns system-wide transactions across all accounts for treasury management and live audits.

- **Method & Route:** `GET /transactions`
- **Query Parameters:** `type` (optional), `page` (default 1), `limit` (default 10), `search` (narration, reference, or account name).
- **Response (`200 OK`):**
  ```json
  {
    "data": [
      {
        "id": "e21908...",
        "account_id": "7f0c18d4...",
        "account_name": "Jane Doe",
        "type": "debit",
        "amount": 50.0,
        "description": "Monthly subscription share",
        "reference_id": "XFER-9902",
        "created_at": "2026-10-28T01:10:00.000000+00:00"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 10,
      "total_records": 1,
      "total_pages": 1
    }
  }
  ```

---

### 8. Immutability Enforcement
Direct modification or deletion of ledger entries is strictly rejected.

- **Method & Route:** `PUT`, `PATCH`, `DELETE` on `/accounts/{account_id}/transactions/{transaction_id}`
- **Response (`405 Method Not Allowed`):**
  ```json
  {
    "error": {
      "code": "TRANSACTION_IMMUTABLE",
      "message": "Transactions cannot be edited or deleted",
      "details": null
    }
  }
  ```

---

### 9. Health Check
Liveness probe utilized by deployment platforms (Railway, Kubernetes, Docker).

- **Method & Route:** `GET /health`
- **Response (`200 OK`):** `{"status": "ok"}`
