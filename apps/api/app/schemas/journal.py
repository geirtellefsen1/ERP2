from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class JournalLineCreate(BaseModel):
    account_id: int
    debit_amount: float = 0
    credit_amount: float = 0
    description: Optional[str] = None


class JournalEntryCreate(BaseModel):
    client_id: int
    entry_date: datetime
    description: str
    posting_period_id: int
    lines: list[JournalLineCreate]


class JournalLineResponse(BaseModel):
    id: int
    account_id: int
    debit_amount: float
    credit_amount: float
    description: Optional[str] = None
    line_number: int

    model_config = {"from_attributes": True}


class JournalEntryResponse(BaseModel):
    id: int
    entry_number: str
    entry_date: datetime
    description: str
    debit_total: float
    credit_total: float
    status: str
    is_balanced: bool
    client_id: int
    ai_validation_notes: Optional[str] = None

    model_config = {"from_attributes": True}


class JournalEntryDetailResponse(JournalEntryResponse):
    lines: list[JournalLineResponse] = []

    model_config = {"from_attributes": True}
