"""
Leave Management — Sprint 16.
Leave balance tracking, application workflow, approval.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal
from app.database import get_db
from app.models import LeaveType, LeaveBalance, LeaveApplication, User
from app.auth import AuthUser, get_current_user

router = APIRouter(prefix="/api/v1/leave", tags=["leave"])


@router.get("/types")
def list_leave_types(country: str = Query("ZA"), db: Session = Depends(get_db)):
    return db.query(LeaveType).filter(LeaveType.country == country).all()


@router.get("/balances", response_model=list)
def get_balances(employee_id: int = Query(...), year: int = Query(default_factory=lambda: datetime.now().year), db: Session = Depends(get_db)):
    return db.query(LeaveBalance).filter(
        LeaveBalance.employee_id == employee_id,
        LeaveBalance.year == year,
    ).all()


@router.post("/apply")
def apply_leave(
    employee_id: int = Query(...),
    leave_type_id: int = Query(...),
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    db: Session = Depends(get_db),
):
    """Apply for leave — calculates days requested."""
    from dateutil.parser import parse
    start = parse(start_date.isoformat())
    end = parse(end_date.isoformat())
    days = (end - start).days + 1

    application = LeaveApplication(
        employee_id=employee_id,
        leave_type_id=leave_type_id,
        start_date=start,
        end_date=end,
        days_requested=Decimal(str(days)),
        status="pending",
    )
    db.add(application)

    # Update pending balance
    balance = db.query(LeaveBalance).filter(
        LeaveBalance.employee_id == employee_id,
        LeaveBalance.leave_type_id == leave_type_id,
        LeaveBalance.year == start.year,
    ).first()
    if balance:
        balance.pending_days = balance.pending_days + Decimal(str(days))

    db.commit()
    return {"id": application.id, "status": application.status, "days_requested": days}


@router.post("/{application_id}/approve")
def approve_leave(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
):
    app = db.query(LeaveApplication).filter(LeaveApplication.id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    app.status = "approved"
    app.approved_by = current_user.sub

    # Move from pending to used
    balance = db.query(LeaveBalance).filter(
        LeaveBalance.employee_id == app.employee_id,
        LeaveBalance.leave_type_id == app.leave_type_id,
        LeaveBalance.year == app.start_date.year,
    ).first()
    if balance:
        balance.pending_days = max(balance.pending_days - app.days_requested, Decimal("0"))
        balance.used_days = balance.used_days + app.days_requested

    db.commit()
    return {"id": application_id, "status": "approved"}


@router.post("/{application_id}/reject")
def reject_leave(
    application_id: int,
    reason: str = "",
    db: Session = Depends(get_db),
):
    app = db.query(LeaveApplication).filter(LeaveApplication.id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    app.status = "rejected"
    db.commit()
    return {"id": application_id, "status": "rejected"}


@router.get("/applications")
def list_applications(
    employee_id: int = Query(...),
    status: str = Query(None),
    year: int = Query(default_factory=lambda: datetime.now().year),
    db: Session = Depends(get_db),
):
    q = db.query(LeaveApplication).filter(LeaveApplication.employee_id == employee_id)
    if status:
        q = q.filter(LeaveApplication.status == status)
    return q.order_by(LeaveApplication.start_date.desc()).all()
