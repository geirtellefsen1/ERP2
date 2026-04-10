from sqlalchemy import Column, Integer, ForeignKey, Numeric
from app.models.base import BaseModel


class Payslip(BaseModel):
    """Individual payslip linked to a payroll run and employee."""
    __tablename__ = "payslips"

    payroll_run_id = Column(Integer, ForeignKey("payroll_runs.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    gross_salary = Column(Numeric(12, 2))
    paye_tax = Column(Numeric(12, 2))
    uif_employee = Column(Numeric(12, 2))
    sdl = Column(Numeric(12, 2))
    eti = Column(Numeric(12, 2))
    net_salary = Column(Numeric(12, 2))
