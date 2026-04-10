"""Norway-specific payroll models for Sprint 15."""

from sqlalchemy import Column, Integer, String, ForeignKey, Numeric, Boolean, DateTime
from app.models.base import BaseModel


class PayrollRunNO(BaseModel):
    """Norway-specific payroll run extensions."""
    __tablename__ = "payroll_runs_no"

    payroll_run_id = Column(Integer, ForeignKey("payroll_runs.id"), unique=True)
    a_melding_submitted = Column(Boolean, default=False)
    a_melding_id = Column(String(50), nullable=True)
    a_melding_submitted_at = Column(DateTime(timezone=True), nullable=True)
    otp_percentage = Column(Numeric(5, 2), default=2.0)


class EmployeeNOSettings(BaseModel):
    """Norway-specific employee settings (OTP, pension, holiday pay)."""
    __tablename__ = "employee_no_settings"

    employee_id = Column(Integer, nullable=False)  # References employees table
    otp_member = Column(Boolean, default=True)
    pension_percentage = Column(Numeric(5, 2), default=2.0)
    holiday_pay_type = Column(String(20), default="percentage")
