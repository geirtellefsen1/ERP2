from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.routers import whatsapp

# Create a test app with the whatsapp router included
# (main.py will integrate this router later; tests must be self-contained)
test_app = FastAPI()
test_app.include_router(whatsapp.router)

client = TestClient(test_app)


def test_list_messages_requires_auth():
    response = client.get("/whatsapp/messages")
    assert response.status_code == 401


def test_get_message_requires_auth():
    response = client.get("/whatsapp/messages/1")
    assert response.status_code == 401


def test_list_conversations_requires_auth():
    response = client.get("/whatsapp/conversations")
    assert response.status_code == 401


def test_send_message_requires_auth():
    response = client.post(
        "/whatsapp/send",
        json={"phone_number": "+27821234567", "client_id": 1, "content": "Hello"},
    )
    assert response.status_code == 401


def test_webhook_endpoint_exists():
    """The webhook endpoint should exist and accept POST (no auth required).
    It will fail with 422 if no valid payload is provided, proving the route is registered."""
    response = client.post("/whatsapp/webhook", json={})
    # 422 means the route exists but payload validation failed — expected
    assert response.status_code == 422


def test_schema_imports():
    """Verify all schema classes can be imported."""
    from app.schemas.whatsapp import (
        WhatsAppMessageResponse,
        WhatsAppMessageList,
        WhatsAppWebhookPayload,
        SendMessageRequest,
        ConversationFlowResponse,
        ConversationFlowList,
    )
    assert WhatsAppMessageResponse is not None
    assert WhatsAppMessageList is not None
    assert WhatsAppWebhookPayload is not None
    assert SendMessageRequest is not None
    assert ConversationFlowResponse is not None
    assert ConversationFlowList is not None


def test_model_imports():
    """Verify model classes can be imported."""
    from app.models.whatsapp import WhatsAppMessage, ConversationFlow
    assert WhatsAppMessage.__tablename__ == "whatsapp_messages"
    assert ConversationFlow.__tablename__ == "conversation_flows"
