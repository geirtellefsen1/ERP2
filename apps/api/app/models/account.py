from sqlalchemy import Column, String, ForeignKey, Integer, Numeric, Index
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Account(BaseModel):
    """Chart of Accounts entry for a client"""
    __tablename__ = "accounts"

    agency_id = Column(Integer, ForeignKey("agencies.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    account_number = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    account_type = Column(String(50), nullable=False)  # asset, liability, equity, revenue, expense
    parent_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    is_active = Column(String(10), default="active")
    balance = Column(Numeric(19, 2), default=0)
    description = Column(String(500), nullable=True)

    agency = relationship("Agency", back_populates="accounts")
    client = relationship("Client", back_populates="accounts")
    parent = relationship("Account", remote_side="Account.id")
    transactions = relationship("Transaction", back_populates="account")

    __table_args__ = (
        Index("idx_accounts_agency_id", "agency_id"),
        Index("idx_accounts_client_id", "client_id"),
        Index("idx_accounts_account_number", "account_number"),
    )
