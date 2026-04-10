from sqlalchemy import Column, String, ForeignKey, Integer, Numeric, DateTime, Boolean, Index
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Transaction(BaseModel):
    """Financial transaction linked to a client account"""
    __tablename__ = "transactions"

    agency_id = Column(Integer, ForeignKey("agencies.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    transaction_date = Column(DateTime(timezone=True), nullable=False)
    description = Column(String(500), nullable=False)
    amount = Column(Numeric(19, 2), nullable=False)
    debit_amount = Column(Numeric(19, 2), default=0)
    credit_amount = Column(Numeric(19, 2), default=0)
    reference = Column(String(255), nullable=True)
    transaction_type = Column(String(50), nullable=False)  # journal, payment, invoice, bank
    status = Column(String(50), default="posted")  # draft, posted, reversed
    matched = Column(Boolean, default=False)
    matched_invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=True)

    client = relationship("Client", back_populates="transactions")
    account = relationship("Account", back_populates="transactions")

    __table_args__ = (
        Index("idx_transactions_agency_id", "agency_id"),
        Index("idx_transactions_client_id", "client_id"),
        Index("idx_transactions_account_id", "account_id"),
        Index("idx_transactions_date", "transaction_date"),
    )
