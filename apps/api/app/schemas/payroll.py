from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal


# ── Employee Schemas ──────────────────────────────────────────────────


class EmployeeCreate(BaseModel):
    client_id: int
    employee_number: Optional[str] = None
    full_name: str
    id_number: Optional[str] = None
    tax_number: Optional[str] = None
    monthly_salary: Decimal
    country: Optional[str] = "ZA"


class EmployeeResponse(BaseModel):
    id: int
    agency_id: int
    client_id: int
    user_id: Optional[int] = None
    employee_number: Optional[str] = None
    full_name: str
    id_number: Optional[str] = None
    tax_number: Optional[str] = None
    monthly_salary: Decimal
    is_active: bool
    country: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── Payslip Schemas ───────────────────────────────────────────────────


class PayslipResponse(BaseModel):
    id: int
    payroll_run_id: int
    employee_id: int
    client_id: int
    gross_salary: Optional[Decimal] = None
    paye_tax: Optional[Decimal] = None
    uif_employee: Optional[Decimal] = None
    sdl: Optional[Decimal] = None
    eti: Optional[Decimal] = None
    net_salary: Optional[Decimal] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── Payroll Run Schemas ───────────────────────────────────────────────


class PayrollRunCreate(BaseModel):
    client_id: int
    period_start: datetime
    period_end: datetime


class PayrollRunResponse(BaseModel):
    id: int
    client_id: int
    period_start: datetime
    period_end: datetime
    status: Optional[str] = None
    total_gross: Optional[Decimal] = None
    total_paye: Optional[Decimal] = None
    total_uif: Optional[Decimal] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class PayrollRunDetailResponse(PayrollRunResponse):
    payslips: list[PayslipResponse] = []

    model_config = {"from_attributes": True}


# ── Calculation Schemas ───────────────────────────────────────────────


class PayrollCalculateResponse(BaseModel):
    run_id: int
    status: str
    employees_processed: int
    total_gross: Decimal
    total_paye: Decimal
    total_uif: Decimal


class EMP201Response(BaseModel):
    total_employees: int
    total_gross: Decimal
    total_paye: Decimal
    total_uif: Decimal
    total_sdl: Decimal
    total_eti: Decimal
    total_liability: Decimal
