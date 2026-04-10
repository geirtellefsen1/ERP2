from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime


class CashflowForecastCreate(BaseModel):
    client_id: int
    opening_balance: float
    avg_weekly_receipts: float
    avg_weekly_payments: float


class CashflowForecastResponse(BaseModel):
    id: int
    client_id: int
    forecast_date: date
    end_date: Optional[date] = None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CashflowForecastLineResponse(BaseModel):
    week_commencing: date
    opening_balance: float
    receipts: float
    payments: float
    closing_balance: float
    alert_flag: bool

    model_config = {"from_attributes": True}


class ForecastAlertResponse(BaseModel):
    id: int
    alert_type: Optional[str] = None
    severity: Optional[str] = None
    week_number: Optional[int] = None
    narrative: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CashflowForecastDetail(BaseModel):
    forecast: CashflowForecastResponse
    lines: List[CashflowForecastLineResponse]
    alerts: List[ForecastAlertResponse]


class ForecastAlertList(BaseModel):
    items: List[ForecastAlertResponse]
    total: int
