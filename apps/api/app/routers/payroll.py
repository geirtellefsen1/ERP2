from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from decimal import Decimal

from app.db.session import get_db
from app.auth.middleware import get_current_user, security
from app.models.payroll import PayrollRun
from app.models.employee import Employee
from app.models.payslip import Payslip
from app.schemas.payroll import (
    PayrollRunCreate,
    PayrollRunResponse,
    PayrollRunDetailResponse,
    PayrollCalculateResponse,
    EmployeeCreate,
    EmployeeResponse,
    PayslipResponse,
    EMP201Response,
)
from app.services.payroll_sa import calculate_payslip, generate_emp201

router = APIRouter(prefix="/payroll", tags=["payroll"])


# ── Payroll Runs ──────────────────────────────────────────────────────


@router.post("/runs", response_model=PayrollRunResponse, status_code=status.HTTP_201_CREATED)
async def create_payroll_run(
    payload: PayrollRunCreate,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Create a new draft payroll run."""
    ctx = await get_current_user(credentials)
    run = PayrollRun(
        client_id=payload.client_id,
        period_start=payload.period_start,
        period_end=payload.period_end,
        status="draft",
        total_gross=Decimal("0"),
        total_paye=Decimal("0"),
        total_uif=Decimal("0"),
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


@router.get("/runs", response_model=list[PayrollRunResponse])
async def list_payroll_runs(
    client_id: int | None = None,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """List payroll runs, optionally filtered by client_id."""
    ctx = await get_current_user(credentials)
    query = db.query(PayrollRun)
    if client_id is not None:
        query = query.filter(PayrollRun.client_id == client_id)
    runs = query.order_by(PayrollRun.created_at.desc()).all()
    return runs


@router.get("/runs/{run_id}", response_model=PayrollRunDetailResponse)
async def get_payroll_run(
    run_id: int,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Get a payroll run with its payslips."""
    ctx = await get_current_user(credentials)
    run = db.query(PayrollRun).filter(PayrollRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Payroll run not found")

    payslips = db.query(Payslip).filter(Payslip.payroll_run_id == run_id).all()

    return PayrollRunDetailResponse(
        id=run.id,
        client_id=run.client_id,
        period_start=run.period_start,
        period_end=run.period_end,
        status=run.status,
        total_gross=run.total_gross,
        total_paye=run.total_paye,
        total_uif=run.total_uif,
        created_at=run.created_at,
        updated_at=run.updated_at,
        payslips=[PayslipResponse.model_validate(p) for p in payslips],
    )


# ── Calculate ─────────────────────────────────────────────────────────


@router.post("/runs/{run_id}/calculate", response_model=PayrollCalculateResponse)
async def calculate_payroll_run(
    run_id: int,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Calculate payslips for all active employees in the payroll run's client."""
    ctx = await get_current_user(credentials)
    run = db.query(PayrollRun).filter(PayrollRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Payroll run not found")
    if run.status != "draft":
        raise HTTPException(status_code=400, detail="Can only calculate draft runs")

    # Remove any existing payslips for this run
    db.query(Payslip).filter(Payslip.payroll_run_id == run_id).delete()

    employees = db.query(Employee).filter(
        Employee.client_id == run.client_id,
        Employee.is_active == True,
    ).all()

    total_gross = Decimal("0")
    total_paye = Decimal("0")
    total_uif = Decimal("0")

    for emp in employees:
        result = calculate_payslip(emp.monthly_salary)
        payslip = Payslip(
            payroll_run_id=run_id,
            employee_id=emp.id,
            client_id=run.client_id,
            gross_salary=result["gross_salary"],
            paye_tax=result["paye_tax"],
            uif_employee=result["uif_employee"],
            sdl=result["sdl"],
            eti=result["eti"],
            net_salary=result["net_salary"],
        )
        db.add(payslip)
        total_gross += result["gross_salary"]
        total_paye += result["paye_tax"]
        total_uif += result["uif_employee"]

    run.status = "processing"
    run.total_gross = total_gross
    run.total_paye = total_paye
    run.total_uif = total_uif
    db.commit()

    return PayrollCalculateResponse(
        run_id=run.id,
        status=run.status,
        employees_processed=len(employees),
        total_gross=total_gross,
        total_paye=total_paye,
        total_uif=total_uif,
    )


# ── Approve ───────────────────────────────────────────────────────────


@router.post("/runs/{run_id}/approve", response_model=PayrollRunResponse)
async def approve_payroll_run(
    run_id: int,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Approve a payroll run (must be in processing status)."""
    ctx = await get_current_user(credentials)
    run = db.query(PayrollRun).filter(PayrollRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Payroll run not found")
    if run.status not in ("processing", "draft"):
        raise HTTPException(status_code=400, detail="Run cannot be approved from current status")

    run.status = "submitted"
    db.commit()
    db.refresh(run)
    return run


# ── Employees ─────────────────────────────────────────────────────────


@router.get("/employees", response_model=list[EmployeeResponse])
async def list_employees(
    client_id: int | None = None,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """List employees, optionally filtered by client_id."""
    ctx = await get_current_user(credentials)
    query = db.query(Employee).filter(Employee.agency_id == ctx.agency_id)
    if client_id is not None:
        query = query.filter(Employee.client_id == client_id)
    return query.all()


@router.post("/employees", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
async def create_employee(
    payload: EmployeeCreate,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Create a new employee."""
    ctx = await get_current_user(credentials)
    employee = Employee(
        agency_id=ctx.agency_id,
        client_id=payload.client_id,
        employee_number=payload.employee_number,
        full_name=payload.full_name,
        id_number=payload.id_number,
        tax_number=payload.tax_number,
        monthly_salary=payload.monthly_salary,
        country=payload.country or "ZA",
        is_active=True,
    )
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


# ── EMP201 Export ─────────────────────────────────────────────────────


@router.get("/runs/{run_id}/emp201", response_model=EMP201Response)
async def get_emp201(
    run_id: int,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Get EMP201 export data for a payroll run."""
    ctx = await get_current_user(credentials)
    run = db.query(PayrollRun).filter(PayrollRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Payroll run not found")

    payslips = db.query(Payslip).filter(Payslip.payroll_run_id == run_id).all()

    slip_dicts = []
    for p in payslips:
        slip_dicts.append({
            "gross_salary": p.gross_salary or Decimal("0"),
            "paye_tax": p.paye_tax or Decimal("0"),
            "uif_employee": p.uif_employee or Decimal("0"),
            "uif_employer": p.uif_employee or Decimal("0"),  # mirror for EMP201
            "sdl": p.sdl or Decimal("0"),
            "eti": p.eti or Decimal("0"),
        })

    summary = generate_emp201(slip_dicts)
    return EMP201Response(**summary)
