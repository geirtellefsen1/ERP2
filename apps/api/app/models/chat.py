from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, JSON
from sqlalchemy.sql import func
from app.models.base import BaseModel


class ChatSession(BaseModel):
    __tablename__ = "agent_chat_sessions"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    title = Column(String(255), nullable=True)


class ChatMessage(BaseModel):
    __tablename__ = "agent_chat_messages"

    session_id = Column(Integer, ForeignKey("agent_chat_sessions.id"), nullable=False)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    citations = Column(JSON, nullable=True)  # [{type: 'journal_entry', id: 'xxx'}, ...]
    token_count = Column(Integer, nullable=True)


class ChatRateLimit(BaseModel):
    __tablename__ = "chat_rate_limits"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    messages_today = Column(Integer, default=0)
    last_reset = Column(DateTime(timezone=True), server_default=func.now())
