import os
from typing import Optional

from fastapi import Depends, FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import services
from .db import atomic, connect, init_db
from .errors import register_handlers
from .schemas import (
    AccountCreate,
    AccountOut,
    AdminHistoryOut,
    BalanceOut,
    HistoryOut,
    TransactionCreate,
    TransactionOut,
    TransferCreate,
    TransferOut,
    TxType,
)



def create_app(db_path: Optional[str] = None) -> FastAPI:
    if not db_path:
        db_path = os.getenv("LEDGER_DB")
        if not db_path:
            if os.path.isdir("/data"):
                db_path = "/data/ledger.db"
            elif os.path.exists("ledger.db"):
                db_path = "ledger.db"
            elif os.path.exists("../ledger.db"):
                db_path = "../ledger.db"
            else:
                db_path = "ledger.db"
    init_db(db_path)

    app = FastAPI(title="Transaction Ledger API", version="1.0.0")
    register_handlers(app)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def get_conn():
        conn = connect(db_path)
        try:
            yield conn
        finally:
            conn.close()

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/accounts", response_model=list[AccountOut])
    def list_accounts(conn=Depends(get_conn)):
        return services.list_accounts(conn)

    @app.post("/accounts", response_model=AccountOut, status_code=201)
    def create_account(body: AccountCreate, conn=Depends(get_conn)):
        with atomic(conn):
            return services.create_account(conn, body.name)

    @app.get("/accounts/{account_id}/balance", response_model=BalanceOut)
    def get_balance(account_id: str, conn=Depends(get_conn)):
        return services.get_balance(conn, account_id)

    @app.post("/accounts/{account_id}/transactions", response_model=TransactionOut, status_code=201)
    def add_transaction(account_id: str, body: TransactionCreate, conn=Depends(get_conn)):
        return services.add_transaction(
            conn, account_id, body.type, body.amount, body.description, body.reference_id
        )

    @app.get("/accounts/{account_id}/transactions", response_model=HistoryOut)
    def history(
        account_id: str,
        type: Optional[TxType] = Query(None, description="credit or debit"),
        page: int = Query(1, ge=1),
        limit: int = Query(10, ge=1, le=100),
        start_date: Optional[str] = Query(None, description="Filter from start date (YYYY-MM-DD or ISO)"),
        end_date: Optional[str] = Query(None, description="Filter up to end date (YYYY-MM-DD or ISO)"),
        min_amount: Optional[float] = Query(None, ge=0, description="Minimum transaction amount"),
        max_amount: Optional[float] = Query(None, ge=0, description="Maximum transaction amount"),
        search: Optional[str] = Query(None, description="Search narration or reference ID"),
        conn=Depends(get_conn),
    ):
        return services.get_history(
            conn,
            account_id,
            type,
            page,
            limit,
            start_date=start_date,
            end_date=end_date,
            min_amount=min_amount,
            max_amount=max_amount,
            search=search,
        )

    @app.post("/transfers", response_model=TransferOut, status_code=201)
    def transfer(body: TransferCreate, conn=Depends(get_conn)):
        return services.transfer(
            conn,
            body.from_account_id,
            body.to_account_id,
            body.amount,
            body.description,
            body.reference_id,
        )

    @app.get("/transactions", response_model=AdminHistoryOut)
    def all_transactions(
        type: Optional[TxType] = Query(None, description="credit or debit"),
        page: int = Query(1, ge=1),
        limit: int = Query(10, ge=1, le=100),
        search: Optional[str] = Query(None, description="Search narration, reference ID or account name"),
        conn=Depends(get_conn),
    ):
        return services.get_all_transactions(
            conn,
            type,
            page,
            limit,
            search=search,
        )


    # Transactions are immutable: no PUT/PATCH/DELETE routes exist, and the
    # database blocks UPDATE/DELETE with triggers. Return a clear 405 message.
    @app.api_route(
        "/accounts/{account_id}/transactions/{transaction_id}",
        methods=["PUT", "PATCH", "DELETE"],
        include_in_schema=False,
    )
    def immutable(account_id: str, transaction_id: str):
        return JSONResponse(
            status_code=405,
            content={
                "error": {
                    "code": "TRANSACTION_IMMUTABLE",
                    "message": "Transactions cannot be edited or deleted",
                    "details": None,
                }
            },
        )

    # Mount frontend static single-page application if dist is built
    dist_candidates = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static")),
        os.path.abspath(os.path.join(os.getcwd(), "frontend", "dist")),
        os.path.abspath(os.path.join(os.getcwd(), "dist")),
    ]
    dist_dir = next(
        (d for d in dist_candidates if os.path.isdir(d) and os.path.isfile(os.path.join(d, "index.html"))),
        None,
    )

    if dist_dir:
        assets_dir = os.path.join(dist_dir, "assets")
        if os.path.isdir(assets_dir):
            app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

        @app.get("/", include_in_schema=False)
        def serve_index():
            return FileResponse(os.path.join(dist_dir, "index.html"))

        @app.get("/{full_path:path}", include_in_schema=False)
        def serve_spa(full_path: str):
            api_prefixes = ("accounts", "transfers", "transactions", "health", "docs", "redoc", "openapi.json")
            if any(full_path == p or full_path.startswith(f"{p}/") for p in api_prefixes):
                return JSONResponse(
                    status_code=404,
                    content={"error": {"code": "NOT_FOUND", "message": "Endpoint not found"}},
                )
            file_path = os.path.join(dist_dir, full_path)
            if os.path.isfile(file_path):
                return FileResponse(file_path)
            return FileResponse(os.path.join(dist_dir, "index.html"))

    return app


app = create_app()
