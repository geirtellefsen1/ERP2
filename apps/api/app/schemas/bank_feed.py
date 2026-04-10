from pydantic import BaseModel
from datetime import datetime
from typing import Optional


# --- Bank Connection schemas ---

class BankConnectionCreate(BaseModel):
    client_id: int
    provider: str
    bank_name: str
    account_number_masked: str


class BankConnectionResponse(BaseModel):
    id: int
    agency_id: int
    client_id: int
    provider: str
    bank_name: str
    account_number_masked: str
    status: str
    last_synced_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Bank Transaction schemas ---

class BankTransactionResponse(BaseModel):
    id: int
    agency_id: int
    client_id: int
    bank_connection_id: int
    external_id: str
    transaction_date: datetime
    description: str
    amount: float
    currency: str
    category: Optional[str] = None
    match_status: str
    matched_transaction_id: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class BankSyncRequest(BaseModel):
    connection_id: int


class BankSyncResponse(BaseModel):
    connection_id: int
    transactions_imported: int
    message: str


# --- Reconciliation schemas ---

class AutoMatchResponse(BaseModel):
    matches_found: int
    matched_pairs: list[dict]


class MatchSuggestion(BaseModel):
    bank_transaction_id: int
    suggested_transaction_id: int
    confidence: float
    amount: float
    date_diff_days: int


class MatchSuggestionsResponse(BaseModel):
    bank_transaction_id: int
    suggestions: list[MatchSuggestion]


class ConfirmMatchRequest(BaseModel):
    bank_transaction_id: int
    transaction_id: int


class ConfirmMatchResponse(BaseModel):
    bank_transaction_id: int
    transaction_id: int
    status: str
    message: str


class ExcludeRequest(BaseModel):
    bank_transaction_id: int


class ExcludeResponse(BaseModel):
    bank_transaction_id: int
    status: str
    message: str
