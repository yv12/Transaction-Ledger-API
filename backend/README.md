# Transaction Ledger API — Backend Service

A high-integrity, ACID-compliant ledger backend built with **Python 3.10+**, **FastAPI**, and **SQLite**. Supports account creation, credit/debit transactions, balance queries, paginated audit history, and atomic peer-to-peer money transfers.

---

## 🚀 Running Backend Locally

### 1. Prerequisites
- Python 3.10+
- `pip`

### 2. Setup Virtual Environment & Install Dependencies
```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv venv

# On Linux / macOS:
source venv/bin/activate
# On Windows (PowerShell / Command Prompt):
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Launch Development Server
```bash
uvicorn app.main:app --reload --port 8000
```
- API Base URL: `http://127.0.0.1:8000`
- Interactive Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc Documentation: `http://127.0.0.1:8000/redoc`
- Health check: `http://127.0.0.1:8000/health`

---

## 🧪 Running Automated Test Suite

The test suite contains 30 comprehensive test cases covering validations, atomicity, race conditions, edge cases, duplicate protection, immutability triggers, system-wide transactions, and transfers.

```bash
# Make sure you are in backend/ with venv active
python -m pytest -v
```

---

## 📁 Backend Project Structure

```
backend/
├── app/
│   ├── __init__.py      # Package marker
│   ├── db.py            # SQLite schema, atomic() context manager, immutability triggers
│   ├── errors.py        # Centralized AppError hierarchy and standardized error handler
│   ├── main.py          # FastAPI application, route handlers, CORS, immutability routes
│   ├── schemas.py       # Pydantic v2 validation models and response schemas
│   └── services.py      # Core business logic: atomic transactions, transfers, pagination
├── tests/
│   ├── __init__.py
│   └── test_api.py      # 29 Pytest unit, integration, and concurrency tests
├── requirements.txt     # Locked production and testing dependencies
└── README.md            # Backend technical documentation
```

---

## 📖 API Documentation

All amounts are non-negative decimals with up to 2 decimal places (converted to integer cents internally for zero floating-point drift). All timestamps are UTC in ISO 8601 format.

### 1. Create Account
- **Method & Path:** `POST /accounts`
- **Request Body:**
  ```json
  {
    "name": "Jane Doe"
  }
  ```
- **Rules:**
  - `name` is required, whitespace-trimmed, 1–100 characters.
  - Client cannot provide initial balance (`extra="forbid"` returns `422`).
  - Balance initializes to strictly `0.0`.
- **Response `201 Created`:**
  ```json
  {
    "id": "7f0c18d4-5ea7-4b19-b7b5-23c5cf8c39e2",
    "name": "Jane Doe",
    "balance": 0.0,
    "created_at": "2026-10-27T12:00:00.123456+00:00"
  }
  ```

---

### 2. Add Transaction
- **Method & Path:** `POST /accounts/{account_id}/transactions`
- **Request Body:**
  ```json
  {
    "type": "credit",
    "amount": 100.50,
    "description": "Consulting invoice",
    "reference_id": "inv-2026-001"
  }
  ```
- **Rules:**
  - `type` must be `"credit"` or `"debit"`.
  - `amount` must be greater than 0.
  - `reference_id` must be unique per account.
  - Debits fail with `422 INSUFFICIENT_BALANCE` if `balance < amount`.
- **Response `201 Created`:**
  ```json
  {
    "id": "c138fd90-...",
    "account_id": "7f0c18d4-...",
    "type": "credit",
    "amount": 100.50,
    "description": "Consulting invoice",
    "reference_id": "inv-2026-001",
    "created_at": "2026-10-27T12:05:00.654321+00:00"
  }
  ```

---

### 3. Get Account Balance
- **Method & Path:** `GET /accounts/{account_id}/balance`
- **Response `200 OK`:**
  ```json
  {
    "account_id": "7f0c18d4-...",
    "balance": 100.50
  }
  ```
- **Error `404 Not Found`:** Returned if `account_id` does not exist.

---

### 4. Get Transaction History
- **Method & Path:** `GET /accounts/{account_id}/transactions`
- **Query Parameters:**
  - `type` (optional): `"credit"` | `"debit"` (omitted returns both).
  - `page` (optional, default `1`): page number `>= 1`.
  - `limit` (optional, default `10`): page size between `1` and `100`.
- **Sorting:** Latest-first order (`ORDER BY created_at DESC`).
- **Response `200 OK`:**
  ```json
  {
    "account_id": "7f0c18d4-...",
    "data": [
      {
        "id": "c138fd90-...",
        "account_id": "7f0c18d4-...",
        "type": "credit",
        "amount": 100.50,
        "description": "Consulting invoice",
        "reference_id": "inv-2026-001",
        "created_at": "2026-10-27T12:05:00.654321+00:00"
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

### 5. Money Transfer (Bonus)
- **Method & Path:** `POST /transfers`
- **Request Body:**
  ```json
  {
    "from_account_id": "7f0c18d4-...",
    "to_account_id": "9b1e22f1-...",
    "amount": 50.00,
    "description": "Monthly rent share",
    "reference_id": "txfer-1002"
  }
  ```
- **Atomicity:** Debit from source and credit to destination occur within a single database transaction lock (`BEGIN IMMEDIATE`). If any step fails, everything is rolled back.
- **Response `201 Created`:**
  ```json
  {
    "from_transaction": { "...": "..." },
    "to_transaction": { "...": "..." },
    "from_balance": 50.50,
    "to_balance": 150.00
  }
  ```

---

## 🔒 Data Integrity & Immutability Guarantees

1. **Integer Minor Units:** All financial values are stored as integer cents to avoid IEEE 754 floating-point inaccuracies.
2. **Immediate Write Locking:** `BEGIN IMMEDIATE` acquires exclusive write locks prior to checking balances, avoiding double-spend race conditions under concurrent requests.
3. **Database Level Immutability:** SQLite triggers `trg_tx_no_update` and `trg_tx_no_delete` prevent any `UPDATE` or `DELETE` on the `transactions` table.
4. **Idempotency & Duplicate Guard:** Compound `UNIQUE (account_id, reference_id)` database constraint guarantees idempotency. Repeated requests return `409 DUPLICATE_TRANSACTION` with the existing transaction without changing balances.

---

## 📝 Design Assumptions

1. **Currencies:** Single domestic fiat currency without exchange rates.
2. **Monetary Precision:** Quantized strictly to 2 decimal places (cents).
3. **Identifier Format:** Server assigns UUIDv4 for both accounts and transactions.
4. **Transaction Immutability:** Completed ledger entries can never be modified or erased; corrections must be posted as new offsetting transactions.
5. **Transfers:** Use the same `reference_id` on both ledger sides; transfers to self (`from == to`) are rejected with `422`.
