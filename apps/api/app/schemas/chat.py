from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime


class ChatSessionCreate(BaseModel):
    client_id: Optional[int] = None
    title: Optional[str] = None


class ChatSessionResponse(BaseModel):
    id: int
    user_id: int
    client_id: Optional[int] = None
    title: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatSessionList(BaseModel):
    items: list[ChatSessionResponse]
    total: int


class ChatMessageCreate(BaseModel):
    session_id: int
    content: str


class ChatMessageResponse(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    citations: Optional[list[Any]] = None
    token_count: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatMessageList(BaseModel):
    items: list[ChatMessageResponse]
    total: int


class SendMessageRequest(BaseModel):
    message: str


class SendMessageResponse(BaseModel):
    id: int
    role: str
    content: str
    citations: Optional[list[Any]] = None


class ChatSessionDetail(BaseModel):
    id: int
    user_id: int
    client_id: Optional[int] = None
    title: Optional[str] = None
    created_at: datetime
    messages: list[ChatMessageResponse]

    model_config = {"from_attributes": True}
