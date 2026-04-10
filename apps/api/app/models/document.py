from sqlalchemy import Column, String, ForeignKey, Integer, Text, Index
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Document(BaseModel):
    """Document uploaded for a client (invoices, receipts, statements)"""
    __tablename__ = "documents"

    agency_id = Column(Integer, ForeignKey("agencies.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    document_type = Column(String(50), nullable=False)  # invoice, receipt, statement, contract
    file_name = Column(String(255), nullable=False)
    file_url = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    status = Column(String(50), default="pending")  # pending, extracted, posted, failed
    extraction_confidence = Column(Integer, nullable=True)  # 0-100
    extracted_data = Column(Text, nullable=True)  # JSON string

    agency = relationship("Agency", back_populates="documents")
    client = relationship("Client", back_populates="documents")

    __table_args__ = (
        Index("idx_documents_agency_id", "agency_id"),
        Index("idx_documents_client_id", "client_id"),
        Index("idx_documents_status", "status"),
    )
