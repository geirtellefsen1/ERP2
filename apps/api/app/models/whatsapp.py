from sqlalchemy import Column, String, Integer, ForeignKey, Text, Float, Boolean, DateTime, JSON, Index
from app.models.base import BaseModel


class WhatsAppMessage(BaseModel):
    """WhatsApp message log for inbound and outbound messages."""
    __tablename__ = "whatsapp_messages"

    phone_number = Column(String(20), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    direction = Column(String(20), default="inbound")  # inbound/outbound
    content = Column(Text)
    status = Column(String(20), default="pending")  # pending/processing/delivered/failed
    confidence_score = Column(Float, nullable=True)
    escalated_to_agent_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    escalation_reason = Column(Text, nullable=True)

    __table_args__ = (
        Index("idx_whatsapp_messages_client_id", "client_id"),
        Index("idx_whatsapp_messages_phone_number", "phone_number"),
        Index("idx_whatsapp_messages_status", "status"),
    )


class ConversationFlow(BaseModel):
    """Tracks multi-step WhatsApp conversation flows."""
    __tablename__ = "conversation_flows"

    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    phone_number = Column(String(20))
    flow_type = Column(String(50))  # document_submission/query/payslip_request/expense_claim/invoice_approval
    state = Column(JSON, nullable=True)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_conversation_flows_client_id", "client_id"),
        Index("idx_conversation_flows_phone_number", "phone_number"),
    )
