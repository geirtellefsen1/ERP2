from sqlalchemy import Column, String, Integer, ForeignKey, Boolean, DateTime, Numeric, Index
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class JournalEntry(BaseModel):
    """Journal entry header"""
    __tablename__ = "journal_entries"

    agency_id = Column(Integer, ForeignKey("agencies.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    posting_period_id = Column(Integer, ForeignKey("posting_periods.id"), nullable=False)
    entry_number = Column(String(50), unique=True, nullable=False)
    entry_date = Column(DateTime(timezone=True), nullable=False)
    description = Column(String(500), nullable=False)
    debit_total = Column(Numeric(19, 2), default=0, nullable=False)
    credit_total = Column(Numeric(19, 2), default=0, nullable=False)
    status = Column(String(20), default="draft", nullable=False)  # draft, balanced, posted, reversed
    is_balanced = Column(Boolean, default=False, nullable=False)
    reversed_by = Column(Integer, nullable=True)
    ai_validation_notes = Column(String(1000), nullable=True)

    agency = relationship("Agency")
    client = relationship("Client")
    posting_period = relationship("PostingPeriod", back_populates="journal_entries")
    lines = relationship("JournalEntryLine", back_populates="entry", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_journal_entries_agency_id", "agency_id"),
        Index("idx_journal_entries_client_id", "client_id"),
        Index("idx_journal_entries_entry_number", "entry_number"),
        Index("idx_journal_entries_status", "status"),
    )


class JournalEntryLine(BaseModel):
    """Individual line item in a journal entry"""
    __tablename__ = "journal_entry_lines"

    entry_id = Column(Integer, ForeignKey("journal_entries.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    debit_amount = Column(Numeric(19, 2), default=0, nullable=False)
    credit_amount = Column(Numeric(19, 2), default=0, nullable=False)
    description = Column(String(500), nullable=True)
    line_number = Column(Integer, nullable=False)

    entry = relationship("JournalEntry", back_populates="lines")
    account = relationship("Account")

    __table_args__ = (
        Index("idx_journal_entry_lines_entry_id", "entry_id"),
        Index("idx_journal_entry_lines_account_id", "account_id"),
    )
