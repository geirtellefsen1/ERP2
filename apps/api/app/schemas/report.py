from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class AccountTotal(BaseModel):
    account_id: int
    account_number: str
    account_name: str
    total: float


class ProfitLossResponse(BaseModel):
    client_id: int
    period_start: datetime
    period_end: datetime
    revenue: list[AccountTotal]
    expenses: list[AccountTotal]
    total_revenue: float
    total_expenses: float
    net_income: float


class BalanceSheetSection(BaseModel):
    accounts: list[AccountTotal]
    total: float


class BalanceSheetResponse(BaseModel):
    client_id: int
    as_at: datetime
    assets: BalanceSheetSection
    liabilities: BalanceSheetSection
    equity: BalanceSheetSection


class TrialBalanceRow(BaseModel):
    account_id: int
    account_number: str
    account_name: str
    debit_total: float
    credit_total: float


class TrialBalanceResponse(BaseModel):
    client_id: int
    rows: list[TrialBalanceRow]
    total_debits: float
    total_credits: float


class AgedBucket(BaseModel):
    invoice_id: int
    invoice_number: str
    amount: float
    due_date: datetime
    days_overdue: int


class AgedDebtorsResponse(BaseModel):
    client_id: int
    as_at: datetime
    current: list[AgedBucket]
    days_30: list[AgedBucket]
    days_60: list[AgedBucket]
    days_90: list[AgedBucket]
    days_90_plus: list[AgedBucket]
    total: float
