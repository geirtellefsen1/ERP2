from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import extract
from app.db.session import get_db
from app.auth.middleware import get_current_user, security
from app.models.leave import LeaveType, LeaveBalance, LeaveRequest
from app.schemas.leave import (
    LeaveTypeCreate,
    LeaveTypeResponse,
    LeaveBalanceResponse,
    LeaveRequestCreate,
    LeaveRequestResponse,
    LeaveRequestList,
    LeaveCalendarResponse,
    LeaveCalendarEntry,
    BusinessDaysResponse,
    RejectRequest,
)
from app.services.leave_service import (
    calculate_business_days,
    check_balance,
    submit_request,
    approve_request,
    reject_request,
)
from typing import Optional
from datetime import date
from pydantic import BaseModel

router = APIRouter(prefix="/leave", tags=["leave"])


class CalculateDaysInput(BaseModel):
    start_date: date
    end_date: date


# --- Leave Types ---


@router.post("/types", response_model=LeaveTypeResponse, status_code=201)
async def create_leave_type(
    data: LeaveTypeCreate,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Create a new leave type."""
    ctx = await get_current_user(credentials)
    leave_type = LeaveType(
        client_id=data.client_id,
        name=data.name,
        code=data.code,
        is_paid=data.is_paid,
        carries_over=data.carries_over,
        max_balance=data.max_balance,
    )
    db.add(leave_type)
    db.commit()
    db.refresh(leave_type)
    return leave_type


@router.get("/types", response_model=list[LeaveTypeResponse])
async def list_leave_types(
    client_id: Optional[int] = Query(None),
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """List leave types, optionally filtered by client."""
    ctx = await get_current_user(credentials)
    query = db.query(LeaveType)
    if client_id:
        query = query.filter(LeaveType.client_id == client_id)
    return query.order_by(LeaveType.name).all()


# --- Leave Requests ---


@router.post("/requests", response_model=LeaveRequestResponse, status_code=201)
async def create_leave_request(
    data: LeaveRequestCreate,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Submit a new leave request."""
    ctx = await get_current_user(credentials)
    employee_id = int(ctx.user_id) if isinstance(ctx.user_id, str) else ctx.user_id
    return submit_request(
        employee_id=employee_id,
        leave_type_id=data.leave_type_id,
        start_date=data.start_date,
        end_date=data.end_date,
        db=db,
    )


@router.get("/requests", response_model=LeaveRequestList)
async def list_leave_requests(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """List leave requests with optional status filter."""
    ctx = await get_current_user(credentials)
    query = db.query(LeaveRequest)
    if status:
        query = query.filter(LeaveRequest.status == status)

    total = query.count()
    items = query.order_by(LeaveRequest.created_at.desc()).offset(
        (page - 1) * per_page
    ).limit(per_page).all()

    return LeaveRequestList(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/requests/{request_id}", response_model=LeaveRequestResponse)
async def get_leave_request(
    request_id: int,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Get a single leave request by ID."""
    ctx = await get_current_user(credentials)
    leave_request = db.query(LeaveRequest).filter(LeaveRequest.id == request_id).first()
    if not leave_request:
        raise HTTPException(status_code=404, detail="Leave request not found")
    return leave_request


@router.post("/requests/{request_id}/approve", response_model=LeaveRequestResponse)
async def approve_leave_request(
    request_id: int,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Approve a leave request."""
    ctx = await get_current_user(credentials)
    approver_id = int(ctx.user_id) if isinstance(ctx.user_id, str) else ctx.user_id
    return approve_request(request_id, approver_id, db)


@router.post("/requests/{request_id}/reject", response_model=LeaveRequestResponse)
async def reject_leave_request(
    request_id: int,
    body: RejectRequest,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Reject a leave request."""
    ctx = await get_current_user(credentials)
    return reject_request(request_id, body.reason, db)


# --- Leave Balance ---


@router.get("/balance/{employee_id}", response_model=list[LeaveBalanceResponse])
async def get_leave_balance(
    employee_id: int,
    year: Optional[int] = Query(None),
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Get leave balances for an employee."""
    ctx = await get_current_user(credentials)
    query = db.query(LeaveBalance).filter(LeaveBalance.employee_id == employee_id)
    if year:
        query = query.filter(LeaveBalance.calendar_year == year)
    return query.all()


# --- Utilities ---


@router.post("/calculate-days", response_model=BusinessDaysResponse)
async def calculate_days(
    data: CalculateDaysInput,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Calculate business days between two dates."""
    ctx = await get_current_user(credentials)
    days = calculate_business_days(data.start_date, data.end_date)
    return BusinessDaysResponse(
        start_date=data.start_date,
        end_date=data.end_date,
        business_days=days,
    )


@router.get("/calendar/{year}/{month}", response_model=LeaveCalendarResponse)
async def get_leave_calendar(
    year: int,
    month: int,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Get leave calendar for a given month."""
    ctx = await get_current_user(credentials)
    requests = db.query(LeaveRequest).filter(
        LeaveRequest.status.in_(["submitted", "approved"]),
        extract("year", LeaveRequest.start_date) == year,
        extract("month", LeaveRequest.start_date) == month,
    ).all()

    entries = [
        LeaveCalendarEntry(
            employee_id=r.employee_id,
            leave_type_id=r.leave_type_id,
            start_date=r.start_date,
            end_date=r.end_date,
            business_days=r.business_days,
            status=r.status,
        )
        for r in requests
    ]

    return LeaveCalendarResponse(month=month, year=year, requests=entries)
