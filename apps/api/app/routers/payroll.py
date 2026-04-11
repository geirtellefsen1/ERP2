"""
South Africa Payroll — PAYE, UIF, SDL, ETI calculations and payslip generation.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal
from app.database import get_db
from app.models import Employee, PayrollPeriod, Payslip, PayrollRun, Client
from app.auth import AuthUser, get_current_user

router = APIRouter(prefix="/api/v1/payroll", tags=["payroll"])


# ─── 2026 SA Tax Tables (monthly) ──────────────────────────────────────────────

def calculate_paye(annual_taxable_income: Decimal) -> Decimal:
    """
    SA PAYE calculation — 2026 tax brackets (monthly taxable income).
    Rebates and threshold applied externally.
    """
    annual = float(annual_taxable_income)
    if annual <= 0:
        return Decimal("0")

    # Tax brackets (R per year)
    if annual <= 237100:
        tax = annual * 0.18
    elif annual <= 370500:
        tax = 237100 * 0.18 + (annual - 237100) * 0.26
    elif annual <= 512800:
        tax = 237100 * 0.18 + (370500 - 237100) * 0.26 + (annual - 370500) * 0.31
    elif annual <= 673000:
        tax = 237100 * 0.18 + (370500 - 237100) * 0.26 + (512800 - 370500) * 0.31 + (annual - 512800) * 0.36
    elif annual <= 857900:
        tax = 237100 * 0.18 + (370500 - 237100) * 0.26 + (512800 - 370500) * 0.31 + (673000 - 512800) * 0.36 + (annual - 673000) * 0.39
    elif annual <= 1817000:
        tax = 237100 * 0.18 + (370500 - 237100) * 0.26 + (512800 - 370500) * 0.31 + (673000 - 512800) * 0.36 + (857900 - 673000) * 0.39 + (annual - 857900) * 0.41
    else:
        tax = 237100 * 0.18 + (370500 - 237100) * 0.26 + (512800 - 370500) * 0.31 + (673000 - 512800) * 0.36 + (857900 - 673000) * 0.39 + (1817000 - 857900) * 0.41 + (annual - 1817000) * 0.45

    # Monthly PAYE
    monthly_paye = tax / 12
    # Rebates (2026 — primary rebate ~R17,235/year)
    primary_rebate_monthly = Decimal("1436")  # Approximate primary rebate / 12
    paye = max(monthly_paye - float(primary_rebate_monthly), 0)
    return Decimal(str(round(paye, 2)))


def calculate_uif(gross: Decimal) -> tuple[Decimal, Decimal]:
    """
    UIF — 1% employee + 1% employer (capped at R177/month each).
    UIF contribution = 2% of remuneration up to the ceiling.
    Ceiling: R17,712/month (2026).
    """
    ceiling = Decimal("17712")
    uifable = min(gross, ceiling)
    rate = Decimal("0.02")  # 1% employee + 1% employer
    total = float(uifable * rate)
    return Decimal(str(round(total / 2, 2))), Decimal(str(round(total / 2, 2)))


def calculate_sdl(gross: Decimal) -> Decimal:
    """
    Skills Development Levy (SDL) — 1% of remuneration.
    Employer only. Exempts employees earning below R6,600/month.
    """
    if gross < Decimal("6600"):
        return Decimal("0")
    return Decimal(str(round(float(gross) * 0.01, 2)))


def calculate_eti(gross: Decimal) -> Decimal:
    """
    Employment Tax Incentive (ETI) — encourages hiring young workers.
    Phase-out starts at R10,570/month.
    """
    if gross > Decimal("22150"):
        return Decimal("0")
    if gross <= Decimal("6490"):
        return Decimal("1500")
    if gross <= Decimal("10840"):
        return Decimal("1250")
    if gross <= Decimal("22150"):
        # Linear phase-out between R10,570 and R22,150
        phase_out = (Decimal("22150") - gross) / (Decimal("22150") - Decimal("10840"))
        return Decimal(str(round(float(Decimal("1250") - phase_out * Decimal("1250")), 2)))
    return Decimal("0")


# ─── Schemas ──────────────────────────────────────────────────────────────────

class EmployeeCreate(BaseModel):
    client_id: int
    first_name: str = Field(max_length=100)
    last_name: str = Field(max_length=100)
    id_number: str | None = None
    tax_number: str | None = None
    uif_number: str | None = None
    employment_type: str = "permanent"
    department: str | None = None
    position: str | None = None
    join_date: datetime
    gross_salary: Decimal  # Monthly gross


class PayslipPreview(BaseModel):
    employee_id: int
    gross_salary: Decimal
    paye: Decimal
    uif_employee: Decimal
    uif_employer: Decimal
    sdl: Decimal
    eti: Decimal
    pension: Decimal
    medical_aid: Decimal
    other_deductions: Decimal
    total_deductions: Decimal
    net_salary: Decimal


class RunPayrollRequest(BaseModel):
    client_id: int
    period_id: int
    employee_ids: list[int]


# ─── Routes ──────────────────────────────────────────────────────────────────

@router.get("/employees", response_model=list)
def list_employees(client_id: int = Query(...), db: Session = Depends(get_db)):
    """List all active employees for a client."""
    return db.query(Employee).filter(
        Employee.client_id == client_id,
        Employee.is_active == True,
    ).order_by(Employee.last_name).all()


@router.post("/employees", response_model=dict, status_code=201)
def create_employee(data: EmployeeCreate, db: Session = Depends(get_db)):
    """Register a new employee."""
    emp = Employee(**data.model_dump(exclude={"gross_salary"}))
    db.add(emp); db.commit(); db.refresh(emp)
    return {"id": emp.id, "name": f"{emp.first_name} {emp.last_name}", "employee_number": emp.employee_number}


@router.get("/periods", response_model=list)
def list_periods(client_id: int = Query(...), year: int | None = None, db: Session = Depends(get_db)):
    q = db.query(PayrollPeriod).filter(PayrollPeriod.client_id == client_id)
    if year:
        q = q.filter(PayrollPeriod.year == year)
    return q.order_by(PayrollPeriod.year.desc(), PayrollPeriod.month.desc()).all()


@router.post("/periods", response_model=dict, status_code=201)
def create_period(client_id: int = Query(...), year: int = Query(...), month: int = Query(...), db: Session = Depends(get_db)):
    """Create a payroll period for a month."""
    start = datetime(year, month, 1)
    if month == 12:
        end = datetime(year + 1, 1, 1)
    else:
        end = datetime(year, month + 1, 1)
    end = end.replace(hour=0, minute=0, second=0)

    existing = db.query(PayrollPeriod).filter(
        PayrollPeriod.client_id == client_id,
        PayrollPeriod.year == year,
        PayrollPeriod.month == month,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Period already exists")

    period = PayrollPeriod(
        client_id=client_id,
        year=year,
        month=month,
        period_start=start,
        period_end=end,
    )
    db.add(period); db.commit(); db.refresh(period)
    return {"id": period.id, "year": year, "month": month, "status": period.status}


@router.post("/calculate")
def calculate_payslip_preview(
    gross_salary: Decimal,
    pension: Decimal = Decimal("0"),
    medical_aid: Decimal = Decimal("0"),
    other_deductions: Decimal = Decimal("0"),
) -> PayslipPreview:
    """
    Calculate PAYE, UIF, SDL, ETI for a given gross salary.
    Used for payslip preview before running payroll.
    """
    paye = calculate_paye(gross_salary * Decimal("12")) / Decimal("12")  # Back to monthly
    uif_e, uif_er = calculate_uif(gross_salary)
    sdl = calculate_sdl(gross_salary)
    eti = calculate_eti(gross_salary)

    total_deductions = paye + uif_e + pension + medical_aid + other_deductions
    net = gross_salary - total_deductions

    return PayslipPreview(
        employee_id=0,
        gross_salary=gross_salary,
        paye=paye,
        uif_employee=uif_e,
        uif_employer=uif_er,
        sdl=sdl,
        eti=eti,
        pension=pension,
        medical_aid=medical_aid,
        other_deductions=other_deductions,
        total_deductions=total_deductions,
        net_salary=net,
    )


@router.post("/run")
def run_payroll(
    data: RunPayrollRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
):
    """
    Run payroll for selected employees in a period.
    Calculates PAYE, UIF, SDL, ETI for each employee.
    """
    client = db.query(Client).filter(
        Client.id == data.client_id,
        Client.agency_id == current_user.agency_id,
    ).first()
    if not client:
        raise HTTPException(status_code=403, detail="Client not found")

    period = db.query(PayrollPeriod).filter(
        PayrollPeriod.id == data.period_id,
        PayrollPeriod.client_id == data.client_id,
    ).first()
    if not period:
        raise HTTPException(status_code=404, detail="Period not found")

    employees = db.query(Employee).filter(
        Employee.id.in_(data.employee_ids),
        Employee.client_id == data.client_id,
    ).all()

    payslips_created = []
    for emp in employees:
        # Get gross from last payslip or use a stored value
        gross = Decimal("25000")  # Default — in production: store per-employee salary

        paye = calculate_paye(gross * Decimal("12")) / Decimal("12")
        uif_e, uif_er = calculate_uif(gross)
        sdl = calculate_sdl(gross)
        eti = calculate_eti(gross)

        total_deductions = paye + uif_e + Decimal("0") + Decimal("0") + Decimal("0")
        net = gross - total_deductions

        payslip = Payslip(
            employee_id=emp.id,
            payroll_run_id=period.id,
            period_id=period.id,
            gross_salary=gross,
            total_earnings=gross,
            paye=paye,
            uif_employee=uif_e,
            uif_employer=uif_er,
            sdl=sdl,
            eti=eti,
            pension=Decimal("0"),
            medical_aid=Decimal("0"),
            other_deductions=Decimal("0"),
            total_deductions=total_deductions,
            net_salary=net,
            status="draft",
        )
        db.add(payslip)
        payslips_created.append(emp.id)

    period.status = "processing"
    db.commit()

    return {
        "period_id": period.id,
        "employees_processed": len(payslips_created),
        "period_status": period.status,
    }


@router.get("/payslips", response_model=list)
def list_payslips(
    period_id: int = Query(...),
    db: Session = Depends(get_db),
):
    """Get all payslips for a payroll period."""
    return db.query(Payslip).filter(Payslip.period_id == period_id).all()
