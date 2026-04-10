from sqlalchemy import Column, String, Integer, ForeignKey, Boolean, DateTime, Index
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class PostingPeriod(BaseModel):
    """Posting period for journal entries"""
    __tablename__ = "posting_periods"

    agency_id = Column(Integer, ForeignKey("agencies.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    period_name = Column(String(100), nullable=False)
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(20), default="open", nullable=False)  # open, closed, locked
    is_locked = Column(Boolean, default=False, nullable=False)

    agency = relationship("Agency")
    client = relationship("Client")
    journal_entries = relationship("JournalEntry", back_populates="posting_period")

    __table_args__ = (
        Index("idx_posting_periods_agency_id", "agency_id"),
        Index("idx_posting_periods_client_id", "client_id"),
    )
