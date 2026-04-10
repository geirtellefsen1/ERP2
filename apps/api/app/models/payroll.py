from sqlalchemy import Column, String, ForeignKey, Integer, Numeric, DateTime, Index
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class PayrollRun(BaseModel):
    """Payroll run for a client"""
    __tablename__ = "payroll_runs"

    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(50), default="draft")  # draft, processing, submitted, paid
    total_gross = Column(Numeric(12, 2), default=0)
    total_paye = Column(Numeric(12, 2), default=0)
    total_uif = Column(Numeric(12, 2), default=0)

    client = relationship("Client", back_populates="payroll_runs")

    __table_args__ = (
        Index("idx_payroll_runs_client_id", "client_id"),
        Index("idx_payroll_runs_status", "status"),
    )
