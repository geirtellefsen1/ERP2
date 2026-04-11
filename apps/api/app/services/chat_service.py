import re
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from app.models.chat import ChatSession, ChatMessage, ChatRateLimit
from app.services.ai_client import ClaudeClient

DAILY_MESSAGE_LIMIT = 100

CHAT_SYSTEM_PROMPT = (
    "You are an AI assistant for a BPO (Business Process Outsourcing) accounting platform called BPO Nexus. "
    "You help users with accounting questions, journal entries, financial reports, and general ERP usage. "
    "When referencing specific records, use the format [source: type/id] (e.g. [source: journal_entry/42]). "
    "Be concise, professional, and helpful."
)


class ChatService:
    def __init__(self, db: Session):
        self.db = db
        self.ai_client = ClaudeClient()

    def create_session(self, user_id: int, client_id: Optional[int] = None, title: Optional[str] = None) -> ChatSession:
        """Create a new chat session."""
        session = ChatSession(
            user_id=user_id,
            client_id=client_id,
            title=title or "New Chat",
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def list_sessions(self, user_id: int) -> list[ChatSession]:
        """List all chat sessions for a user."""
        return (
            self.db.query(ChatSession)
            .filter(ChatSession.user_id == user_id)
            .order_by(ChatSession.id.desc())
            .all()
        )

    def get_session(self, session_id: int, user_id: int) -> Optional[ChatSession]:
        """Get a specific chat session owned by the user."""
        return (
            self.db.query(ChatSession)
            .filter(ChatSession.id == session_id, ChatSession.user_id == user_id)
            .first()
        )

    def get_session_messages(self, session_id: int) -> list[ChatMessage]:
        """Get all messages for a session."""
        return (
            self.db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.id.asc())
            .all()
        )

    def delete_session(self, session_id: int, user_id: int) -> bool:
        """Delete a chat session and its messages."""
        session = self.get_session(session_id, user_id)
        if not session:
            return False

        self.db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
        self.db.delete(session)
        self.db.commit()
        return True

    def store_message(self, session_id: int, role: str, content: str, citations: Optional[list] = None, token_count: Optional[int] = None) -> ChatMessage:
        """Store a chat message."""
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            citations=citations,
            token_count=token_count,
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def check_rate_limit(self, user_id: int) -> bool:
        """Check if user has exceeded the daily message limit. Returns True if allowed."""
        rate_limit = (
            self.db.query(ChatRateLimit)
            .filter(ChatRateLimit.user_id == user_id)
            .first()
        )

        now = datetime.now(timezone.utc)

        if not rate_limit:
            rate_limit = ChatRateLimit(user_id=user_id, messages_today=0)
            self.db.add(rate_limit)
            self.db.commit()
            self.db.refresh(rate_limit)

        # Reset counter if last_reset was a different day
        if rate_limit.last_reset:
            last_reset_date = rate_limit.last_reset
            if hasattr(last_reset_date, "date"):
                last_reset_date = last_reset_date.date()
            if last_reset_date != now.date():
                rate_limit.messages_today = 0
                rate_limit.last_reset = now
                self.db.commit()
                self.db.refresh(rate_limit)

        return rate_limit.messages_today < DAILY_MESSAGE_LIMIT

    def increment_rate_limit(self, user_id: int) -> None:
        """Increment the daily message counter."""
        rate_limit = (
            self.db.query(ChatRateLimit)
            .filter(ChatRateLimit.user_id == user_id)
            .first()
        )
        if rate_limit:
            rate_limit.messages_today = (rate_limit.messages_today or 0) + 1
            self.db.commit()

    @staticmethod
    def extract_citations(text: str) -> list[dict]:
        """Extract citations from response text.

        Supports patterns like:
        - [source: journal_entry/42]
        - [doc: invoice/15]
        """
        citations = []
        patterns = [
            r"\[source:\s*([\w-]+)/([\w-]+)\]",
            r"\[doc:\s*([\w-]+)/([\w-]+)\]",
        ]
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                citations.append({"type": match[0], "id": match[1]})
        return citations

    async def get_response(self, session_id: int, user_message: str, user_id: int) -> ChatMessage:
        """Send a message and get an AI response.

        Stores both the user message and assistant response.
        Checks rate limits before processing.
        """
        if not self.check_rate_limit(user_id):
            raise ValueError("Daily message limit exceeded. Please try again tomorrow.")

        # Store user message
        self.store_message(session_id, "user", user_message)
        self.increment_rate_limit(user_id)

        # Build conversation history for context
        messages = self.get_session_messages(session_id)
        history_lines = []
        for msg in messages[-10:]:  # Last 10 messages for context
            history_lines.append(f"{msg.role}: {msg.content}")
        conversation_context = "\n".join(history_lines)

        # Get AI response
        response_text = await self.ai_client.complete(
            system_prompt=CHAT_SYSTEM_PROMPT,
            user_message=conversation_context,
        )

        # Extract citations
        citations = self.extract_citations(response_text)

        # Estimate token count (rough approximation)
        token_count = len(response_text.split()) * 2

        # Store assistant message
        assistant_message = self.store_message(
            session_id, "assistant", response_text, citations=citations or None, token_count=token_count,
        )

        return assistant_message
