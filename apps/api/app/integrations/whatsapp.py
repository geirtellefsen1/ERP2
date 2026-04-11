"""
OpenClaw WhatsApp Integration — conversation flows, webhook handler.
Implements the OpenClaw WhatsApp webhook for BPO Nexus client interactions.

Flow: WhatsApp message → OpenClaw webhook → /api/v1/whatsapp/webhook
→ route to appropriate handler → respond or escalate
"""
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import httpx, json
from app.database import get_db
from app.models import Client, User, ClientContact
from app.auth import AuthUser, get_current_user
from app.config import get_settings

router = APIRouter(prefix="/api/v1/whatsapp", tags=["whatsapp"])
settings = get_settings()


# ─── WhatsApp Message Schemas ─────────────────────────────────────────────────

class WhatsAppMessage(BaseModel):
    from_number: str
    message_id: str
    text: str | None = None
    media_url: str | None = None
    media_type: str | None = None
    timestamp: str


class WhatsAppOutgoing(BaseModel):
    to: str
    message: str
    media_url: str | None = None


# ─── Conversation Context ───────────────────────────────────────────────────────

# In-memory session store (use Redis in production)
CONVERSATION_SESSIONS: dict[str, dict] = {}


def get_or_create_session(phone: str) -> dict:
    if phone not in CONVERSATION_SESSIONS:
        CONVERSATION_SESSIONS[phone] = {
            "step": "welcome",
            "client_contact_id": None,
            "client_id": None,
            "authenticated": False,
            "menu_stack": [],
        }
    return CONVERSATION_SESSIONS[phone]


# ─── Menu Structure ────────────────────────────────────────────────────────────

MAIN_MENU = """
🏢 Welcome to BPO Nexus

How can we help you today?

1️⃣ 📄 Upload a Document
2️⃣ 💳 View Invoices
3️⃣ 📊 Quick Report
4️⃣ 👤 My Account
5️⃣ 💬 Speak to Agent

Reply with a number (1-5) or your question.
"""


def get_invoice_menu(client_id: int, db: Session) -> str:
    from app.models import Invoice
    pending = db.query(Invoice).filter(
        Invoice.client_id == client_id,
        Invoice.status.in_(["sent", "overdue"]),
    ).count()
    return f"""
💳 Your Invoices

You have {pending} pending invoice(s).

1️⃣ View All Invoices
2️⃣ Pay an Invoice (coming soon)
3️⃣ Download Statement
4️⃣ Back to Main Menu

Reply with a number.
"""


# ─── Message Handlers ───────────────────────────────────────────────────────────

def handle_authenticated_message(text: str, session: dict, db: Session) -> str:
    """Handle message when user is authenticated."""
    client_id = session.get("client_id")
    step = session.get("step", "menu")

    if step == "awaiting_document_category":
        session["step"] = "awaiting_document"
        return f"📄 Great, category: {text}. Now please send the document file."

    if text.strip() == "5":
        return "💬 Connecting you to an agent... We have notified the BPO team. They will respond shortly."

    if text.strip() in ["1", "01"]:
        session["step"] = "document_upload"
        return """
📄 Document Upload

Please send us your document and include a brief description.

Categories available:
• Bank Statement
• Invoice
• Contract
• Payslip
• Tax Return
• Other

Send the file now, or reply with the category name.
"""

    if text.strip() in ["2", "02"]:
        if client_id:
            return get_invoice_menu(client_id, db)
        return MAIN_MENU

    if text.strip() in ["3", "03"]:
        session["step"] = "report_request"
        return """
📊 Quick Report

Which report would you like?

1️⃣ Profit & Loss (this month)
2️⃣ Balance Sheet
3️⃣ Cash Flow Summary

Reply with a number.
"""

    if text.strip() in ["4", "04"]:
        session["step"] = "account"
        return """
👤 Your Account

1️⃣ Update Contact Details
2️⃣ Change Notification Preferences
3️⃣ Back to Main Menu

Reply with a number.
"""

    if text.strip() == "4" and step == "account":
        return MAIN_MENU

    # Free text — use Claude to interpret
    return None  # Fall through to AI handler


def handle_unauthenticated_message(text: str, session: dict, db: Session) -> str:
    """Handle message from unauthenticated user — verify identity."""
    if not session.get("awaiting_email"):
        session["step"] = "awaiting_email"
        session["awaiting_email"] = True
        return """
🔐 Please verify your identity.

Reply with your registered email address.
"""
    else:
        # Email received — look up contact
        email = text.strip().lower()
        contact = db.query(ClientContact).filter(
            ClientContact.email == email
        ).first()
        if contact:
            session["authenticated"] = True
            session["client_id"] = contact.client_id
            session["client_contact_id"] = contact.id
            session["awaiting_email"] = False
            return f"✅ Verified! Welcome back, {contact.name}.{MAIN_MENU}"
        else:
            session["awaiting_email"] = False
            return """
❌ We could not find that email address.

Please contact your BPO agent to register your WhatsApp number.
"""


async def call_claude_for_response(
    text: str,
    session: dict,
    client_name: str | None = None,
) -> str:
    """Use Claude to generate contextual response to free-text message."""
    if not settings.claude_api_key:
        return "Thank you for your message. An agent will respond shortly."

    system = f"""
You are a BPO client service assistant for {client_name or 'a BPO client'}.
Keep responses under 150 words.
Be helpful, professional and friendly.
If you cannot answer, suggest speaking to an agent (reply with '5').
"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": settings.claude_api_key,
                    "anthropic-version": "2023-06-01",
                },
                json={
                    "model": "claude-haiku-4-20250514",
                    "max_tokens": 200,
                    "system": system,
                    "messages": [{"role": "user", "content": text}],
                },
            )
            if resp.status_code == 200:
                return resp.json()["content"][0]["text"]
    except Exception:
        pass
    return "Thank you. An agent will follow up shortly."


# ─── Webhook Route ─────────────────────────────────────────────────────────────

@router.post("/webhook")
async def whatsapp_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    OpenClaw WhatsApp webhook — receives messages from OpenClaw and routes them.
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    # OpenClaw sends WhatsApp events as a specific payload format
    # Extract message
    msg_from = body.get("from") or body.get("sender", {}).get("phone")
    msg_id = body.get("message_id", "")
    msg_text = body.get("text", {}).get("body") or body.get("text", "")
    media_url = body.get("media_url") or body.get("media", {}).get("url")
    media_type = body.get("media_type") or body.get("media", {}).get("mime_type")

    if not msg_from:
        return {"ok": True}  # Acknowledge non-message events

    session = get_or_create_session(msg_from)

    # Route message
    if session.get("authenticated"):
        response_text = handle_authenticated_message(msg_text, session, db)
    else:
        response_text = handle_unauthenticated_message(msg_text, session, db)

    # If no specific handler matched, use Claude
    if response_text is None:
        client_name = None
        if session.get("client_id"):
            client = db.query(Client).filter(Client.id == session["client_id"]).first()
            if client:
                client_name = client.name
        response_text = await call_claude_for_response(
            msg_text, session, client_name
        )

    # Send response via OpenClaw (or queue for background)
    response = WhatsAppOutgoing(
        to=msg_from,
        message=response_text,
        media_url=None,
    )

    # In production: POST to OpenClaw messaging API
    # background_tasks.add_task(send_whatsapp_message, response)
    return {"ok": True, "message": response_text}


# ─── Outbound Notification ─────────────────────────────────────────────────────

async def send_whatsapp_message(outgoing: WhatsAppOutgoing) -> bool:
    """
    Send outbound WhatsApp message via OpenClaw API.
    Called by background tasks for automated notifications.
    """
    if not settings.claude_api_key:  # placeholder for OpenClaw token
        return False

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.openclaw.ai/v1/messages",
                headers={
                    "Authorization": f"Bearer {settings.claude_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "to": outgoing.to,
                    "message": outgoing.message,
                    "media_url": outgoing.media_url,
                },
            )
            return resp.status_code in (200, 201)
    except Exception:
        return False


@router.post("/notify/{client_contact_id}")
async def send_notification(
    client_contact_id: int,
    message: str,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
):
    """
    Send a proactive notification to a client contact via WhatsApp.
    Called by agents from the dashboard or by automated workflows.
    """
    contact = db.query(ClientContact).filter(
        ClientContact.id == client_contact_id
    ).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    if not contact.phone:
        raise HTTPException(status_code=400, detail="No phone number for this contact")

    # Remove any non-digit characters from phone
    phone = "".join(c for c in contact.phone if c.isdigit())
    if not phone.startswith("27"):
        phone = "27" + phone.lstrip("0")

    outgoing = WhatsAppOutgoing(to=phone, message=message)
    sent = await send_whatsapp_message(outgoing)
    return {"sent": sent, "contact": contact.name, "phone": phone}


@router.get("/menu")
def get_menu():
    """Return the WhatsApp menu structure for OpenClaw configuration."""
    return {
        "menu": {
            "1": {"label": "Upload Document", "action": "document_upload"},
            "2": {"label": "View Invoices", "action": "invoices"},
            "3": {"label": "Quick Report", "action": "report"},
            "4": {"label": "My Account", "action": "account"},
            "5": {"label": "Speak to Agent", "action": "escalate"},
        },
        "main_menu": MAIN_MENU,
    }
