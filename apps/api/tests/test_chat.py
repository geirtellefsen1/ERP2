from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.routers import chat

# Create a test app with the chat router included
# (main.py will integrate this router later; tests must be self-contained)
test_app = FastAPI()
test_app.include_router(chat.router)

client = TestClient(test_app)


def test_create_session_requires_auth():
    response = client.post(
        "/chat/sessions",
        json={"title": "Test Session"},
    )
    assert response.status_code == 401


def test_list_sessions_requires_auth():
    response = client.get("/chat/sessions")
    assert response.status_code == 401


def test_get_session_requires_auth():
    response = client.get("/chat/sessions/1")
    assert response.status_code == 401


def test_send_message_requires_auth():
    response = client.post(
        "/chat/sessions/1/messages",
        json={"message": "Hello"},
    )
    assert response.status_code == 401


def test_delete_session_requires_auth():
    response = client.delete("/chat/sessions/1")
    assert response.status_code == 401


def test_chat_schemas_import():
    """Test that chat schemas can be imported and instantiated."""
    from app.schemas.chat import (
        ChatSessionCreate,
        ChatSessionResponse,
        ChatSessionList,
        ChatMessageCreate,
        ChatMessageResponse,
        ChatMessageList,
        SendMessageRequest,
        SendMessageResponse,
    )

    create = ChatSessionCreate(client_id=1, title="Test")
    assert create.client_id == 1
    assert create.title == "Test"

    create_optional = ChatSessionCreate()
    assert create_optional.client_id is None
    assert create_optional.title is None

    msg_create = ChatMessageCreate(session_id=1, content="Hello")
    assert msg_create.session_id == 1
    assert msg_create.content == "Hello"

    send_req = SendMessageRequest(message="Hi there")
    assert send_req.message == "Hi there"


def test_chat_service_module_loads():
    """Test that the chat service module loads and key classes exist."""
    from app.services.chat_service import ChatService, DAILY_MESSAGE_LIMIT

    assert DAILY_MESSAGE_LIMIT == 100
    assert hasattr(ChatService, "create_session")
    assert hasattr(ChatService, "get_response")
    assert hasattr(ChatService, "extract_citations")


def test_chat_service_extract_citations():
    """Test citation extraction from text."""
    from app.services.chat_service import ChatService

    text = "See [source: journal_entry/42] and [doc: invoice/15] for details."
    citations = ChatService.extract_citations(text)

    assert len(citations) == 2
    assert {"type": "journal_entry", "id": "42"} in citations
    assert {"type": "invoice", "id": "15"} in citations


def test_chat_service_extract_citations_empty():
    """Test citation extraction with no citations."""
    from app.services.chat_service import ChatService

    text = "There are no citations in this text."
    citations = ChatService.extract_citations(text)
    assert citations == []


def test_chat_models_import():
    """Test that chat models can be imported."""
    from app.models.chat import ChatSession, ChatMessage, ChatRateLimit

    assert ChatSession.__tablename__ == "agent_chat_sessions"
    assert ChatMessage.__tablename__ == "agent_chat_messages"
    assert ChatRateLimit.__tablename__ == "chat_rate_limits"
