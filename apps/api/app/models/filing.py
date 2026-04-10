from app.models.base import BaseModel
from sqlalchemy import Column, Integer, String, ForeignKey, Date, DateTime, Text
from sqlalchemy.dialects.postgresql import JSON


class FilingRecord(BaseModel):
    __tablename__ = "filing_records"

    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    jurisdiction = Column(String(10), nullable=False)  # 'NO', 'ZA', 'UK', 'EU'
    filing_type = Column(String(50), nullable=False)   # 'VAT', 'PAYROLL', 'ITR'
    period_start = Column(Date)
    period_end = Column(Date)
    status = Column(String(20), default="draft")  # draft/submitted/accepted/rejected
    submission_id = Column(String(100), nullable=True)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    response_data = Column(JSON, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)


class FilingDeadline(BaseModel):
    __tablename__ = "filing_deadlines"

    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    jurisdiction = Column(String(10), nullable=False)
    filing_type = Column(String(50), nullable=False)
    due_date = Column(Date, nullable=False)
    frequency = Column(String(20))  # monthly/quarterly/annual
    reminder_days_before = Column(Integer, default=7)
