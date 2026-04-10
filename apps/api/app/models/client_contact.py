from sqlalchemy import Column, String, Boolean, ForeignKey, Integer
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class ClientContact(BaseModel):
    """Contact person at a client company"""
    __tablename__ = "client_contacts"

    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255))
    phone = Column(String(50))
    role = Column(String(100))
    is_primary = Column(Boolean, default=False)

    client = relationship("Client", back_populates="contacts")
