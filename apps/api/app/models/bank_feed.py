from sqlalchemy import Column, String, ForeignKey, Integer, Numeric, DateTime, Text, Index
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class BankConnection(BaseModel):
    """Bank connection for open-banking feed"""
    __tablename__ = "bank_connections"

    agency_id = Column(Integer, ForeignKey("agencies.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    provider = Column(String(50), nullable=False)  # e.g. "truelayer"
    bank_name = Column(String(255), nullable=False)
    account_number_masked = Column(String(50), nullable=False)
    status = Column(String(20), default="connected", nullable=False)  # connected, disconnected, error
    access_token_encrypted = Column(Text, nullable=True)
    refresh_token_encrypted = Column(Text, nullable=True)
    last_synced_at = Column(DateTime(timezone=True), nullable=True)

    agency = relationship("Agency")
    client = relationship("Client")
    transactions = relationship("BankTransaction", back_populates="bank_connection")

    __table_args__ = (
        Index("idx_bank_connections_agency_id", "agency_id"),
        Index("idx_bank_connections_client_id", "client_id"),
    )


class BankTransaction(BaseModel):
    """Bank transaction imported from a bank feed"""
    __tablename__ = "bank_transactions"

    agency_id = Column(Integer, ForeignKey("agencies.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    bank_connection_id = Column(Integer, ForeignKey("bank_connections.id"), nullable=False)
    external_id = Column(String(255), unique=True, nullable=False)
    transaction_date = Column(DateTime(timezone=True), nullable=False)
    description = Column(String(500), nullable=False)
    amount = Column(Numeric(19, 2), nullable=False)
    currency = Column(String(3), default="ZAR", nullable=False)
    category = Column(String(100), nullable=True)
    match_status = Column(String(20), default="unmatched", nullable=False)  # unmatched, matched, excluded
    matched_transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)

    agency = relationship("Agency")
    client = relationship("Client")
    bank_connection = relationship("BankConnection", back_populates="transactions")
    matched_transaction = relationship("Transaction")

    __table_args__ = (
        Index("idx_bank_transactions_agency_id", "agency_id"),
        Index("idx_bank_transactions_client_id", "client_id"),
        Index("idx_bank_transactions_connection_id", "bank_connection_id"),
        Index("idx_bank_transactions_match_status", "match_status"),
    )
