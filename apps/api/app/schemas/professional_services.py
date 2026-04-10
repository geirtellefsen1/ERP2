from pydantic import BaseModel
from typing import Optional, List
from datetime import date, time, datetime
from decimal import Decimal


# --- Matter schemas ---

class MatterCreate(BaseModel):
    client_id: int
    code: Optional[str] = None
    name: str
    matter_type: Optional[str] = None
    client_reference: Optional[str] = None
    opened_date: Optional[date] = None
    responsible_fee_earner_id: Optional[int] = None


class MatterResponse(BaseModel):
    id: int
    client_id: int
    code: Optional[str] = None
    name: str
    matter_type: Optional[str] = None
    client_reference: Optional[str] = None
    opened_date: Optional[date] = None
    closed_date: Optional[date] = None
    responsible_fee_earner_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class MatterList(BaseModel):
    items: List[MatterResponse]
    total: int


# --- TimeEntry schemas ---

class TimeEntryCreate(BaseModel):
    matter_id: int
    date: date
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    description: Optional[str] = None
    billable: bool = True


class TimeEntryResponse(BaseModel):
    id: int
    matter_id: int
    fee_earner_id: int
    date: date
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    units: Optional[Decimal] = None
    description: Optional[str] = None
    billable: bool
    billed: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class TimeEntryList(BaseModel):
    items: List[TimeEntryResponse]
    total: int


# --- BillingRate schemas ---

class BillingRateCreate(BaseModel):
    client_id: int
    fee_earner_grade: Optional[str] = None
    matter_type: Optional[str] = None
    hourly_rate: Decimal
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None


class BillingRateResponse(BaseModel):
    id: int
    client_id: int
    fee_earner_grade: Optional[str] = None
    matter_type: Optional[str] = None
    hourly_rate: Decimal
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class BillingRateList(BaseModel):
    items: List[BillingRateResponse]
    total: int


# --- WIP schemas ---

class WIPAgingResponse(BaseModel):
    buckets_0_30: Decimal
    buckets_31_60: Decimal
    buckets_61_90: Decimal
    buckets_over_90: Decimal


# --- Utilisation schemas ---

class UtilisationResponse(BaseModel):
    fee_earner: str
    total_hours: Decimal
    billable_hours: Decimal
    utilisation_pct: Decimal


# --- TrustTransaction schemas ---

class TrustTransactionCreate(BaseModel):
    client_id: int
    matter_id: Optional[int] = None
    transaction_type: str  # receipt/disbursement
    amount: Decimal
    description: Optional[str] = None
    bank_reference: Optional[str] = None
    transaction_date: date


class TrustTransactionResponse(BaseModel):
    id: int
    client_id: int
    matter_id: Optional[int] = None
    transaction_type: str
    amount: Decimal
    description: Optional[str] = None
    bank_reference: Optional[str] = None
    transaction_date: date
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class TrustTransactionList(BaseModel):
    items: List[TrustTransactionResponse]
    total: int


# --- Disbursement schemas ---

class DisbursementCreate(BaseModel):
    matter_id: int
    date: date
    description: Optional[str] = None
    amount: Decimal
    to_be_rebilled: bool = True
    rebilled_amount: Optional[Decimal] = None


class DisbursementResponse(BaseModel):
    id: int
    matter_id: int
    date: date
    description: Optional[str] = None
    amount: Decimal
    to_be_rebilled: bool
    rebilled_amount: Optional[Decimal] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class DisbursementList(BaseModel):
    items: List[DisbursementResponse]
    total: int
