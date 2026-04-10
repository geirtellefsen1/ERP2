from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional
from decimal import Decimal


class LeaveTypeCreate(BaseModel):
    client_id: int
    name: str
    code: Optional[str] = None
    is_paid: bool = True
    carries_over: bool = False
    max_balance: Optional[Decimal] = None


class LeaveTypeResponse(BaseModel):
    id: int
    client_id: int
    name: str
    code: Optional[str] = None
    is_paid: bool
    carries_over: bool
    max_balance: Optional[Decimal] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class LeaveBalanceResponse(BaseModel):
    id: int
    employee_id: int
    leave_type_id: int
    calendar_year: int
    opening_balance: Decimal
    entitlements: Decimal
    used: Decimal
    closing_balance: Decimal
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class LeaveRequestCreate(BaseModel):
    leave_type_id: int
    start_date: date
    end_date: date


class LeaveRequestResponse(BaseModel):
    id: int
    employee_id: int
    leave_type_id: int
    start_date: date
    end_date: date
    business_days: int
    status: str
    approver_id: Optional[int] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class LeaveRequestList(BaseModel):
    items: list[LeaveRequestResponse]
    total: int
    page: int
    per_page: int


class LeaveCalendarEntry(BaseModel):
    employee_id: int
    leave_type_id: int
    start_date: date
    end_date: date
    business_days: int
    status: str

    model_config = {"from_attributes": True}


class LeaveCalendarResponse(BaseModel):
    month: int
    year: int
    requests: list[LeaveCalendarEntry]


class BusinessDaysResponse(BaseModel):
    start_date: date
    end_date: date
    business_days: int


class RejectRequest(BaseModel):
    reason: str
