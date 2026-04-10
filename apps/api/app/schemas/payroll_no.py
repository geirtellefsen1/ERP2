"""Pydantic v2 schemas for Norway payroll endpoints."""

from pydantic import BaseModel
from decimal import Decimal
from typing import Optional


class NOCalculateRequest(BaseModel):
    """Request body for calculating a Norwegian payslip."""
    gross_salary: Decimal
    pension_percentage: Decimal = Decimal("2.0")

    model_config = {"from_attributes": True}


class NOPayslipResponse(BaseModel):
    """Calculated payslip breakdown for Norway."""
    gross_salary: Decimal
    otp_pension: Decimal
    trinnskatt: Decimal
    trygdeavgift: Decimal
    income_tax: Decimal
    holiday_pay_accrual: Decimal
    employer_ni: Decimal
    net_salary: Decimal

    model_config = {"from_attributes": True}


class AMeldingRequest(BaseModel):
    """Request body for A-melding generation."""
    org_number: str
    period: str  # e.g. "2026-03"
    employee_count: int = 1
    total_gross: Decimal = Decimal("0")

    model_config = {"from_attributes": True}


class AMeldingResponse(BaseModel):
    """Response containing generated A-melding XML."""
    xml_content: str
    period: str
    org_number: str

    model_config = {"from_attributes": True}


class EmployeeNOSettingsResponse(BaseModel):
    """Norway-specific employee settings response."""
    id: int
    employee_id: int
    otp_member: bool
    pension_percentage: Decimal
    holiday_pay_type: str

    model_config = {"from_attributes": True}


class TaxBracket(BaseModel):
    """A single trinnskatt bracket."""
    step: str
    lower: Decimal
    upper: Optional[Decimal] = None
    rate: Decimal

    model_config = {"from_attributes": True}


class TaxTablesResponse(BaseModel):
    """Current Norwegian tax table data."""
    year: int
    trinnskatt_brackets: list[TaxBracket]
    trygdeavgift_rate: Decimal
    holiday_pay_rate: Decimal
    employer_ni_rate: Decimal
    default_otp_rate: Decimal

    model_config = {"from_attributes": True}
