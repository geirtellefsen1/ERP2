from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal


# --- HospitalityClient ---

class HospitalityClientCreate(BaseModel):
    client_id: int
    pms_system: Optional[str] = None
    currency: str = "USD"


class HospitalityClientResponse(BaseModel):
    id: int
    client_id: int
    pms_system: Optional[str] = None
    pms_api_key: Optional[str] = None
    pms_property_id: Optional[str] = None
    currency: Optional[str] = "USD"
    financial_year_start: Optional[int] = 1
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# --- RoomType ---

class RoomTypeCreate(BaseModel):
    hospitality_client_id: int
    code: str
    name: str
    capacity: Optional[int] = None
    avg_daily_rate: Optional[Decimal] = None


class RoomTypeResponse(BaseModel):
    id: int
    hospitality_client_id: int
    code: Optional[str] = None
    name: Optional[str] = None
    capacity: Optional[int] = None
    avg_daily_rate: Optional[Decimal] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# --- DailyRevenue ---

class DailyRevenueCreate(BaseModel):
    hospitality_client_id: int
    date: date
    room_type_id: Optional[int] = None
    revenue_stream: Optional[str] = None
    rooms_available: int = 0
    rooms_occupied: int = 0
    total_revenue: Decimal = Decimal("0")


class DailyRevenueResponse(BaseModel):
    id: int
    hospitality_client_id: int
    date: date
    room_type_id: Optional[int] = None
    revenue_stream: Optional[str] = None
    rooms_available: Optional[int] = 0
    rooms_occupied: Optional[int] = 0
    total_revenue: Optional[Decimal] = Decimal("0")
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class DailyRevenueList(BaseModel):
    items: List[DailyRevenueResponse]
    total: int


# --- GratuityTip ---

class GratuityTipCreate(BaseModel):
    hospitality_client_id: int
    employee_id: Optional[int] = None
    date: date
    amount: Decimal
    source: Optional[str] = None


class GratuityTipResponse(BaseModel):
    id: int
    hospitality_client_id: int
    employee_id: Optional[int] = None
    date: date
    amount: Decimal
    source: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# --- StockTake ---

class StockTakeCreate(BaseModel):
    hospitality_client_id: int
    date: date
    item_code: Optional[str] = None
    description: Optional[str] = None
    quantity_counted: int = 0
    quantity_expected: int = 0
    unit_cost: Decimal = Decimal("0")


class StockTakeResponse(BaseModel):
    id: int
    hospitality_client_id: int
    date: date
    item_code: Optional[str] = None
    description: Optional[str] = None
    quantity_counted: Optional[int] = 0
    quantity_expected: Optional[int] = 0
    unit_cost: Optional[Decimal] = Decimal("0")
    variance: Optional[Decimal] = Decimal("0")
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# --- Metrics ---

class HospitalityMetricsResponse(BaseModel):
    revpar: Decimal
    adr: Decimal
    occupancy_pct: Decimal
    period: str
