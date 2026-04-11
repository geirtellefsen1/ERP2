from datetime import date, datetime, timezone
from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.leave import LeaveRequest, LeaveBalance, LeaveType


def calculate_business_days(start_date: date, end_date: date) -> int:
    """Count weekdays (Mon-Fri) between start_date and end_date inclusive."""
    if end_date < start_date:
        return 0
    count = 0
    current = start_date
    from datetime import timedelta
    while current <= end_date:
        if current.weekday() < 5:  # Mon=0 ... Fri=4
            count += 1
        current += timedelta(days=1)
    return count


def check_balance(employee_id: int, leave_type_id: int, year: int, db: Session) -> dict:
    """Get leave balance for an employee, leave type, and year."""
    balance = db.query(LeaveBalance).filter(
        LeaveBalance.employee_id == employee_id,
        LeaveBalance.leave_type_id == leave_type_id,
        LeaveBalance.calendar_year == year,
    ).first()

    if not balance:
        return {
            "employee_id": employee_id,
            "leave_type_id": leave_type_id,
            "calendar_year": year,
            "opening_balance": 0,
            "entitlements": 21,
            "used": 0,
            "closing_balance": 21,
        }

    return {
        "employee_id": balance.employee_id,
        "leave_type_id": balance.leave_type_id,
        "calendar_year": balance.calendar_year,
        "opening_balance": float(balance.opening_balance),
        "entitlements": float(balance.entitlements),
        "used": float(balance.used),
        "closing_balance": float(balance.closing_balance),
    }


def submit_request(
    employee_id: int,
    leave_type_id: int,
    start_date: date,
    end_date: date,
    db: Session,
) -> LeaveRequest:
    """Submit a new leave request."""
    if end_date < start_date:
        raise HTTPException(status_code=400, detail="End date must be on or after start date")

    business_days = calculate_business_days(start_date, end_date)
    if business_days == 0:
        raise HTTPException(status_code=400, detail="No business days in selected range")

    # Verify the leave type exists
    leave_type = db.query(LeaveType).filter(LeaveType.id == leave_type_id).first()
    if not leave_type:
        raise HTTPException(status_code=404, detail="Leave type not found")

    leave_request = LeaveRequest(
        employee_id=employee_id,
        leave_type_id=leave_type_id,
        start_date=start_date,
        end_date=end_date,
        business_days=business_days,
        status="submitted",
    )
    db.add(leave_request)
    db.commit()
    db.refresh(leave_request)
    return leave_request


def approve_request(request_id: int, approver_id: int, db: Session) -> LeaveRequest:
    """Approve a leave request and deduct from balance."""
    leave_request = db.query(LeaveRequest).filter(LeaveRequest.id == request_id).first()
    if not leave_request:
        raise HTTPException(status_code=404, detail="Leave request not found")

    if leave_request.status != "submitted":
        raise HTTPException(status_code=400, detail="Only submitted requests can be approved")

    leave_request.status = "approved"
    leave_request.approver_id = approver_id
    leave_request.approved_at = datetime.now(timezone.utc)

    # Deduct from balance
    year = leave_request.start_date.year
    balance = db.query(LeaveBalance).filter(
        LeaveBalance.employee_id == leave_request.employee_id,
        LeaveBalance.leave_type_id == leave_request.leave_type_id,
        LeaveBalance.calendar_year == year,
    ).first()

    if not balance:
        # Auto-create balance record with default 21-day entitlement
        balance = LeaveBalance(
            employee_id=leave_request.employee_id,
            leave_type_id=leave_request.leave_type_id,
            calendar_year=year,
            opening_balance=Decimal("0"),
            entitlements=Decimal("21"),
            used=Decimal("0"),
            closing_balance=Decimal("21"),
        )
        db.add(balance)
        db.flush()

    days = Decimal(str(leave_request.business_days))
    balance.used = (balance.used or Decimal("0")) + days
    balance.closing_balance = (balance.entitlements or Decimal("0")) + (balance.opening_balance or Decimal("0")) - balance.used

    db.commit()
    db.refresh(leave_request)
    return leave_request


def reject_request(request_id: int, reason: str, db: Session) -> LeaveRequest:
    """Reject a leave request with a reason."""
    leave_request = db.query(LeaveRequest).filter(LeaveRequest.id == request_id).first()
    if not leave_request:
        raise HTTPException(status_code=404, detail="Leave request not found")

    if leave_request.status != "submitted":
        raise HTTPException(status_code=400, detail="Only submitted requests can be rejected")

    leave_request.status = "rejected"
    leave_request.rejection_reason = reason

    db.commit()
    db.refresh(leave_request)
    return leave_request
