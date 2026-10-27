from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

TxType = Literal["credit", "debit"]

Amount = Annotated[Decimal, Field(gt=0, max_digits=15, decimal_places=2, allow_inf_nan=False)]
Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
Reference = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
Description = Annotated[str, StringConstraints(strip_whitespace=True, max_length=255)]


class AccountCreate(BaseModel):
    # extra="forbid": a client sending "balance" (or anything else) gets a 422.
    model_config = ConfigDict(extra="forbid")
    name: Name


class TransactionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: TxType
    amount: Amount
    description: Description = ""
    reference_id: Reference


class TransferCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    from_account_id: str = Field(min_length=1)
    to_account_id: str = Field(min_length=1)
    amount: Amount
    description: Description = ""
    reference_id: Reference


class AccountOut(BaseModel):
    id: str
    name: str
    balance: float
    created_at: str


class BalanceOut(BaseModel):
    account_id: str
    balance: float


class TransactionOut(BaseModel):
    id: str
    account_id: str
    type: TxType
    amount: float
    description: str
    reference_id: str
    created_at: str


class PaginationOut(BaseModel):
    page: int
    limit: int
    total_records: int
    total_pages: int


class HistoryOut(BaseModel):
    account_id: str
    data: list[TransactionOut]
    pagination: PaginationOut


class TransferOut(BaseModel):
    from_transaction: TransactionOut
    to_transaction: TransactionOut
    from_balance: float
    to_balance: float


class AdminTransactionOut(BaseModel):
    id: str
    account_id: str
    account_name: str | None = None
    type: TxType
    amount: float
    description: str
    reference_id: str
    created_at: str


class AdminHistoryOut(BaseModel):
    data: list[AdminTransactionOut]
    pagination: PaginationOut

