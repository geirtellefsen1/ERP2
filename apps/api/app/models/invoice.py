from sqlalchemy import Column, String, ForeignKey, Integer, Numeric, DateTime, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import BaseModel


class Invoice(BaseModel):
    """Invoice issued by BPO agency to client"""
    __tablename__ = "invoices"

    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    invoice_number = Column(String(50), unique=True, nullable=False)
    status = Column(String(50), default="draft")  # draft, sent, paid, overdue
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="ZAR")
    due_date = Column(DateTime(timezone=True))
    issued_at = Column(DateTime(timezone=True), server_default=func.now())

    client = relationship("Client", back_populates="invoices")
    line_items = relationship("InvoiceLineItem", back_populates="invoice")

    __table_args__ = (
        Index("idx_invoices_client_id", "client_id"),
        Index("idx_invoices_status", "status"),
    )


class InvoiceLineItem(BaseModel):
    """Line item on an invoice"""
    __tablename__ = "invoice_line_items"

    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    description = Column(Text, nullable=False)
    quantity = Column(Numeric(10, 2), default=1)
    unit_price = Column(Numeric(12, 2), nullable=False)
    total = Column(Numeric(12, 2), nullable=False)

    invoice = relationship("Invoice", back_populates="line_items")
