from app.models.base import BaseModel
from sqlalchemy import Column, Integer, String, ForeignKey, Numeric, Boolean, Date, DateTime, Text
from sqlalchemy.sql import func


class LeaveType(BaseModel):
    __tablename__ = "leave_types"

    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    name = Column(String(50), nullable=False)  # Annual, Sick, Maternity, TOIL
    code = Column(String(20))
    is_paid = Column(Boolean, default=True)
    carries_over = Column(Boolean, default=False)
    max_balance = Column(Numeric(5, 2), nullable=True)


class LeaveBalance(BaseModel):
    __tablename__ = "leave_balances"

    employee_id = Column(Integer, nullable=False)  # References employees
    leave_type_id = Column(Integer, ForeignKey("leave_types.id"), nullable=False)
    calendar_year = Column(Integer, nullable=False)
    opening_balance = Column(Numeric(5, 2), default=0)
    entitlements = Column(Numeric(5, 2), default=21)
    used = Column(Numeric(5, 2), default=0)
    closing_balance = Column(Numeric(5, 2), default=21)


class LeaveRequest(BaseModel):
    __tablename__ = "leave_requests"

    employee_id = Column(Integer, nullable=False)
    leave_type_id = Column(Integer, ForeignKey("leave_types.id"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    business_days = Column(Integer, nullable=False)
    status = Column(String(20), default="draft")  # draft/submitted/approved/rejected
    approver_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)


class LeaveBlackoutDate(BaseModel):
    __tablename__ = "leave_blackout_dates"

    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    name = Column(String(100))
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
