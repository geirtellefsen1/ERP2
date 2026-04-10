from sqlalchemy import Column, String, ForeignKey, Integer, DateTime, Index
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Task(BaseModel):
    """Task in the agency work queue"""
    __tablename__ = "tasks"

    agency_id = Column(Integer, ForeignKey("agencies.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    status = Column(String(50), default="pending")  # pending, in_progress, completed, blocked
    priority = Column(String(50), default="normal")  # low, normal, high, critical
    due_date = Column(DateTime(timezone=True), nullable=True)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)

    agency = relationship("Agency")
    client = relationship("Client")
    assigned_user = relationship("User")

    __table_args__ = (
        Index("idx_tasks_agency_id", "agency_id"),
        Index("idx_tasks_client_id", "client_id"),
        Index("idx_tasks_status", "status"),
    )
