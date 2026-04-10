from app.models.base import BaseModel
from sqlalchemy import Column, Integer, String, ForeignKey, Numeric, Boolean, Date, Time, Text


class Matter(BaseModel):
    __tablename__ = "matters"

    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    code = Column(String(20))
    name = Column(String(255), nullable=False)
    matter_type = Column(String(50))  # corporate/litigation/conveyancing/probate
    client_reference = Column(String(100), nullable=True)
    opened_date = Column(Date, nullable=True)
    closed_date = Column(Date, nullable=True)
    responsible_fee_earner_id = Column(Integer, ForeignKey("users.id"), nullable=True)


class TimeEntry(BaseModel):
    __tablename__ = "time_entries"

    matter_id = Column(Integer, ForeignKey("matters.id"), nullable=False)
    fee_earner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=True)
    end_time = Column(Time, nullable=True)
    units = Column(Numeric(5, 2))  # In 0.1 hour (6-min) increments
    description = Column(Text)
    billable = Column(Boolean, default=True)
    billed = Column(Boolean, default=False)


class BillingRate(BaseModel):
    __tablename__ = "billing_rate_matrix"

    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    fee_earner_grade = Column(String(50))  # partner/senior/junior/paralegal
    matter_type = Column(String(50), nullable=True)
    hourly_rate = Column(Numeric(10, 2), nullable=False)
    effective_from = Column(Date, nullable=True)
    effective_to = Column(Date, nullable=True)


class WIPEntry(BaseModel):
    __tablename__ = "wip_entries"

    matter_id = Column(Integer, ForeignKey("matters.id"), nullable=False)
    period_end = Column(Date, nullable=False)
    hours_performed = Column(Numeric(8, 2), default=0)
    rate_per_hour = Column(Numeric(10, 2), default=0)
    wip_value = Column(Numeric(12, 2), default=0)
    invoice_date = Column(Date, nullable=True)


class TrustTransaction(BaseModel):
    __tablename__ = "trust_account_transactions"

    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    matter_id = Column(Integer, ForeignKey("matters.id"), nullable=True)
    transaction_type = Column(String(20))  # receipt/disbursement
    amount = Column(Numeric(12, 2), nullable=False)
    description = Column(Text)
    bank_reference = Column(String(100), nullable=True)
    transaction_date = Column(Date, nullable=False)


class Disbursement(BaseModel):
    __tablename__ = "disbursements"

    matter_id = Column(Integer, ForeignKey("matters.id"), nullable=False)
    date = Column(Date, nullable=False)
    description = Column(Text)
    amount = Column(Numeric(12, 2), nullable=False)
    to_be_rebilled = Column(Boolean, default=True)
    rebilled_amount = Column(Numeric(12, 2), nullable=True)
