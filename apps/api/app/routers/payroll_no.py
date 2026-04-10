"""Norway payroll API router — Sprint 15."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from decimal import Decimal

from app.db.session import get_db
from app.auth.middleware import get_current_user, security
from app.schemas.payroll_no import (
    NOCalculateRequest,
    NOPayslipResponse,
    AMeldingRequest,
    AMeldingResponse,
    EmployeeNOSettingsResponse,
    TaxBracket,
    TaxTablesResponse,
)
from app.services.payroll_no import (
    calculate_payslip,
    generate_a_melding_xml,
    TRINNSKATT_BRACKETS,
    TRYGDEAVGIFT_RATE,
    HOLIDAY_PAY_RATE,
    EMPLOYER_NI_RATE,
    DEFAULT_OTP_RATE,
)
from app.models.payroll_no import EmployeeNOSettings

router = APIRouter(prefix="/payroll-no", tags=["payroll-no"])


@router.post("/calculate", response_model=NOPayslipResponse)
async def calculate_no_payslip(
    request: NOCalculateRequest,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Calculate a Norwegian payslip from annual gross salary."""
    ctx = await get_current_user(credentials)

    if request.gross_salary <= 0:
        raise HTTPException(status_code=400, detail="Gross salary must be positive")

    result = calculate_payslip(
        gross_salary=request.gross_salary,
        pension_pct=request.pension_percentage,
    )
    return NOPayslipResponse(**result)


@router.get("/tax-tables", response_model=TaxTablesResponse)
async def get_tax_tables(
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Return the current Norwegian tax tables."""
    ctx = await get_current_user(credentials)

    brackets = []
    for i, (lower, upper, rate) in enumerate(TRINNSKATT_BRACKETS, start=1):
        brackets.append(TaxBracket(
            step=f"Step {i}",
            lower=lower,
            upper=upper,
            rate=rate * 100,  # Express as percentage
        ))

    return TaxTablesResponse(
        year=2026,
        trinnskatt_brackets=brackets,
        trygdeavgift_rate=TRYGDEAVGIFT_RATE * 100,
        holiday_pay_rate=HOLIDAY_PAY_RATE * 100,
        employer_ni_rate=EMPLOYER_NI_RATE * 100,
        default_otp_rate=DEFAULT_OTP_RATE * 100,
    )


@router.post("/a-melding/generate", response_model=AMeldingResponse)
async def generate_a_melding(
    request: AMeldingRequest,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Generate a mock A-melding XML document."""
    ctx = await get_current_user(credentials)

    xml = generate_a_melding_xml(
        org_number=request.org_number,
        period=request.period,
        employee_count=request.employee_count,
        total_gross=request.total_gross,
    )
    return AMeldingResponse(
        xml_content=xml,
        period=request.period,
        org_number=request.org_number,
    )


@router.get("/settings/{employee_id}", response_model=EmployeeNOSettingsResponse)
async def get_employee_no_settings(
    employee_id: int,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Get Norway-specific payroll settings for an employee."""
    ctx = await get_current_user(credentials)

    settings = db.query(EmployeeNOSettings).filter(
        EmployeeNOSettings.employee_id == employee_id
    ).first()

    if not settings:
        raise HTTPException(status_code=404, detail="Employee NO settings not found")

    return settings
