from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime


class WhatsAppMessageResponse(BaseModel):
    id: int
    phone_number: str
    client_id: int
    direction: str
    content: Optional[str] = None
    status: str
    confidence_score: Optional[float] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class WhatsAppMessageList(BaseModel):
    items: list[WhatsAppMessageResponse]
    total: int
    page: int
    per_page: int


class WhatsAppWebhookPayload(BaseModel):
    message_sid: str
    from_number: str
    body: str


class SendMessageRequest(BaseModel):
    phone_number: str
    client_id: int
    content: str


class ConversationFlowResponse(BaseModel):
    id: int
    client_id: int
    phone_number: Optional[str] = None
    flow_type: Optional[str] = None
    state: Optional[Any] = None
    completed: bool
    completed_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationFlowList(BaseModel):
    items: list[ConversationFlowResponse]
    total: int
    page: int
    per_page: int
