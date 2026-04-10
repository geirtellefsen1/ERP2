from sqlalchemy import Column, String, Index
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Agency(BaseModel):
    """BPO Agency (the customer - the BPO firm itself)"""
    __tablename__ = "agencies"

    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    subscription_tier = Column(String(50), default="starter")  # starter, growth, enterprise
    countries_enabled = Column(String(255), default="ZA,NO,UK")

    users = relationship("User", back_populates="agency")
    clients = relationship("Client", back_populates="agency")
    accounts = relationship("Account", back_populates="agency")
    documents = relationship("Document", back_populates="agency")

    __table_args__ = (
        Index("idx_agencies_slug", "slug"),
    )
