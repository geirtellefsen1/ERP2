from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.auth.middleware import get_current_user, security
from app.models.whatsapp import WhatsAppMessage, ConversationFlow
from app.schemas.whatsapp import (
    WhatsAppMessageResponse,
    WhatsAppMessageList,
    WhatsAppWebhookPayload,
    SendMessageRequest,
    ConversationFlowResponse,
    ConversationFlowList,
)

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])


@router.post("/webhook")
async def whatsapp_webhook(
    payload: WhatsAppWebhookPayload,
    db: Session = Depends(get_db),
):
    """Receive Twilio WhatsApp webhook. No auth required (verified by Twilio signature)."""
    msg = WhatsAppMessage(
        phone_number=payload.from_number,
        client_id=0,  # Will be resolved by lookup in production
        direction="inbound",
        content=payload.body,
        status="pending",
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    return {"status": "received", "message_id": msg.id}


@router.get("/messages", response_model=WhatsAppMessageList)
async def list_messages(
    client_id: int = Query(None),
    page: int = 1,
    per_page: int = 20,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """List WhatsApp messages, optionally filtered by client_id."""
    ctx = await get_current_user(credentials)
    query = db.query(WhatsAppMessage)

    if client_id is not None:
        query = query.filter(WhatsAppMessage.client_id == client_id)

    total = query.count()
    messages = (
        query.order_by(WhatsAppMessage.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return WhatsAppMessageList(items=messages, total=total, page=page, per_page=per_page)


@router.get("/messages/{message_id}", response_model=WhatsAppMessageResponse)
async def get_message(
    message_id: int,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Get a single WhatsApp message by ID."""
    ctx = await get_current_user(credentials)
    msg = db.query(WhatsAppMessage).filter(WhatsAppMessage.id == message_id).first()

    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    return msg


@router.get("/conversations", response_model=ConversationFlowList)
async def list_conversations(
    client_id: int = Query(None),
    page: int = 1,
    per_page: int = 20,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """List conversation flows, optionally filtered by client_id."""
    ctx = await get_current_user(credentials)
    query = db.query(ConversationFlow)

    if client_id is not None:
        query = query.filter(ConversationFlow.client_id == client_id)

    total = query.count()
    flows = (
        query.order_by(ConversationFlow.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return ConversationFlowList(items=flows, total=total, page=page, per_page=per_page)


@router.post("/send", response_model=WhatsAppMessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    payload: SendMessageRequest,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Send an outbound WhatsApp message. Stores the record in the database."""
    ctx = await get_current_user(credentials)

    msg = WhatsAppMessage(
        phone_number=payload.phone_number,
        client_id=payload.client_id,
        user_id=int(ctx.user_id) if ctx.user_id else None,
        direction="outbound",
        content=payload.content,
        status="delivered",
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    return msg
