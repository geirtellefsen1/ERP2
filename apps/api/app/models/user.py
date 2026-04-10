from sqlalchemy import Column, String, Boolean, ForeignKey, Integer, Index
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class User(BaseModel):
    """User (BPO agent or client user)"""
    __tablename__ = "users"

    agency_id = Column(Integer, ForeignKey("agencies.id"), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(String(50), nullable=False)  # admin, agent, client_admin, client_user
    is_active = Column(Boolean, default=True)
    auth0_id = Column(String(255), unique=True, nullable=True)

    agency = relationship("Agency", back_populates="users")

    __table_args__ = (
        Index("idx_users_agency_id", "agency_id"),
        Index("idx_users_auth0_id", "auth0_id"),
    )
