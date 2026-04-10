from sqlalchemy import Column, String, Boolean, ForeignKey, Integer, Index
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Client(BaseModel):
    """Client company managed by the BPO agency"""
    __tablename__ = "clients"

    agency_id = Column(Integer, ForeignKey("agencies.id"), nullable=False)
    name = Column(String(255), nullable=False)
    registration_number = Column(String(100))
    country = Column(String(3))  # ZA, NO, UK, EU
    industry = Column(String(100))
    fiscal_year_end = Column(String(10))  # e.g. "2024-12-31"
    is_active = Column(Boolean, default=True)
    health_score = Column(String(20), nullable=True)  # excellent, good, fair, poor

    agency = relationship("Agency", back_populates="clients")
    contacts = relationship("ClientContact", back_populates="client")
    invoices = relationship("Invoice", back_populates="client")
    transactions = relationship("Transaction", back_populates="client")
    payroll_runs = relationship("PayrollRun", back_populates="client")
    accounts = relationship("Account", back_populates="client")
    documents = relationship("Document", back_populates="client")

    __table_args__ = (
        Index("idx_clients_agency_id", "agency_id"),
    )
