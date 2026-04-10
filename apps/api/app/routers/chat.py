from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.auth.middleware import get_current_user, security
from app.schemas.chat import (
    ChatSessionCreate,
    ChatSessionResponse,
    ChatSessionList,
    ChatSessionDetail,
    ChatMessageResponse,
    SendMessageRequest,
    SendMessageResponse,
)
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/sessions", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    request: ChatSessionCreate,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Create a new chat session."""
    ctx = await get_current_user(credentials)
    service = ChatService(db)
    session = service.create_session(
        user_id=int(ctx.user_id),
        client_id=request.client_id,
        title=request.title,
    )
    return session


@router.get("/sessions", response_model=ChatSessionList)
async def list_sessions(
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """List all chat sessions for the current user."""
    ctx = await get_current_user(credentials)
    service = ChatService(db)
    sessions = service.list_sessions(user_id=int(ctx.user_id))
    return ChatSessionList(items=sessions, total=len(sessions))


@router.get("/sessions/{session_id}", response_model=ChatSessionDetail)
async def get_session(
    session_id: int,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Get a chat session with all its messages."""
    ctx = await get_current_user(credentials)
    service = ChatService(db)
    session = service.get_session(session_id, user_id=int(ctx.user_id))
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    messages = service.get_session_messages(session_id)
    return ChatSessionDetail(
        id=session.id,
        user_id=session.user_id,
        client_id=session.client_id,
        title=session.title,
        created_at=session.created_at,
        messages=messages,
    )


@router.post("/sessions/{session_id}/messages", response_model=SendMessageResponse)
async def send_message(
    session_id: int,
    request: SendMessageRequest,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Send a message in a chat session and get an AI response."""
    ctx = await get_current_user(credentials)
    service = ChatService(db)

    # Verify session belongs to user
    session = service.get_session(session_id, user_id=int(ctx.user_id))
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    try:
        assistant_message = await service.get_response(
            session_id=session_id,
            user_message=request.message,
            user_id=int(ctx.user_id),
        )
    except ValueError as e:
        raise HTTPException(status_code=429, detail=str(e))

    return SendMessageResponse(
        id=assistant_message.id,
        role=assistant_message.role,
        content=assistant_message.content,
        citations=assistant_message.citations,
    )


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: int,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Delete a chat session and all its messages."""
    ctx = await get_current_user(credentials)
    service = ChatService(db)
    deleted = service.delete_session(session_id, user_id=int(ctx.user_id))
    if not deleted:
        raise HTTPException(status_code=404, detail="Chat session not found")
