# Transaction Ledger System ( Live link to test: transaction-ledger-api-data.up.railway.app)

A complete full-stack transaction ledger platform featuring an ACID-compliant Python/FastAPI backend and a real-time role-based web frontend.

---

## 🏗️ Repository Architecture

The codebase is cleanly separated into two distinct components:

```
ledger-api/
├── backend/                  # Backend REST API Service
│   ├── app/                  # FastAPI core application modules
│   │   ├── db.py             # SQLite engine, atomic context manager, triggers
│   │   ├── errors.py         # Standardized error definitions & handlers
│   │   ├── main.py           # REST endpoints, CORS & routing
│   │   ├── schemas.py        # Pydantic v2 data models & validation
│   │   └── services.py       # Ledger business logic, atomicity & transfers
│   ├── tests/                # Automated Pytest test suite (29 tests)
│   │   └── test_api.py
│   ├── requirements.txt      # Python dependencies
│   └── README.md             # Dedicated backend documentation
│
├── frontend/                 # Frontend Web Client
│   ├── index.html            # Web app shell (Admin & Customer views)
│   ├── src/                  # Vanilla CSS + ES Modules application
│   ├── package.json          # Node dependencies & Vite setup
│   ├── vite.config.js
│   └── README.md             # Dedicated frontend documentation
│
└── README.md                 # Top-level system documentation
```

---

## ⚡ Quickstart Guide

### 1. Launch Backend API (`http://127.0.0.1:8000`)

```bash
cd backend

# Setup environment
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Run server
uvicorn app.main:app --reload --port 8000
```
- **API Swagger Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

### 2. Launch Frontend UI (`http://localhost:5173`)

In a new terminal window:

```bash
cd frontend

# Install dependencies
npm install

# Run dev server
npm run dev
```

Visit [http://localhost:5173](http://localhost:5173) in your browser.

---

## 🚂 Railway Deployment (One-Click / Zero Config)

This repository includes a production-grade multi-stage `Dockerfile` and `railway.json` pre-configured to build the frontend and serve both the REST API and the interactive UI seamlessly from a single unified container on Railway.

### Deploy Steps:
1. Push your repository to **GitHub**.
2. Go to [railway.app](https://railway.app) and click **"New Project"** -> **"Deploy from GitHub repo"**.
3. Select your `ledger-api` repository. Railway will automatically detect the root `Dockerfile`.
4. In Railway project settings:
   - Click **"Generate Domain"** under Networking (e.g. `https://your-ledger.up.railway.app`).
   - *(Optional)* Add a **Persistent Volume** mounted at `/data` if you want your SQLite database to persist across deploys.
5. Visit your generated domain:
   - **Frontend Web UI**: `https://your-ledger.up.railway.app/`
   - **Interactive API Docs (Swagger)**: `https://your-ledger.up.railway.app/docs`
   - **Health Check Endpoint**: `https://your-ledger.up.railway.app/health`

---

## 🧪 Running Automated Tests

Run the backend test suite covering 30 scenarios including edge cases, duplicate checking, concurrency, rollback on failure, system-wide transaction history, and transaction immutability:

```bash
cd backend
python -m pytest -v
```

---

## 📋 Assessment Requirements Checklist

| Requirement | Module | Status |
| :--- | :--- | :---: |
| **1. Create Account API** | `POST /accounts` in `backend/app/main.py` | ✅ Complete |
| **2. Add Transaction API** (Credit / Debit) | `POST /accounts/{id}/transactions` in `backend/app/main.py` | ✅ Complete |
| **3. Get Account Balance** | `GET /accounts/{id}/balance` in `backend/app/main.py` | ✅ Complete |
| **4. Transaction History** (Filtering, Pagination, Sorting) | `GET /accounts/{id}/transactions` in `backend/app/main.py` | ✅ Complete |
| **5. Data Integrity & Immutability** | Database triggers & atomic write locking in `backend/app/db.py` | ✅ Complete |
| **6. Atomic Balance Updates** | Single-transaction `BEGIN IMMEDIATE` in `backend/app/services.py` | ✅ Complete |
| **7. Input Validations** | Pydantic v2 strict schemas in `backend/app/schemas.py` | ✅ Complete |
| **8. Standardized Error Handling** | Unified JSON error contract in `backend/app/errors.py` | ✅ Complete |
| **9. Bonus: Money Transfer** | `POST /transfers` with rollback in `backend/app/services.py` | ✅ Complete |
| **10. Role-Based Frontend UI** | Admin Console + Customer Portal in `frontend/` | ✅ Complete |

---

## 📑 Detailed Documentation Links

- **Backend Specifications & API Guide**: Refer to [backend/README.md](backend/README.md)
- **Frontend Architecture & UX Guide**: Refer to [frontend/README.md](frontend/README.md)


YashVijayvargiya.
