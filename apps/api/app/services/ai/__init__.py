"""
Shared Claude API client wrapper.

Why this layer exists:
- The cashflow narrator, report narrator, anomaly detector, GL coding
  assistant, and agent chat all need to call Claude. Wrapping the API
  in one place keeps prompt engineering, retries, error handling, and
  response parsing in one file instead of scattered across routers.
- Tests need a deterministic mock so they don't depend on network or
  burn API credit on every CI run.
- Production needs the real client.

Usage:
    from app.services.ai import get_claude_client, ClaudeMessage

    client = get_claude_client()
    response = client.complete(
        system="You are a financial analyst...",
        messages=[ClaudeMessage(role="user", content="Summarise this P&L")],
        model="claude-opus-4-6",
        language="nb-NO",
    )
    print(response.text)

Switch to the mock for tests:
    from app.services.ai import MockClaudeClient, set_claude_client

    set_claude_client(MockClaudeClient(canned_response="..."))
"""
from .base import (
    ClaudeMessage,
    ClaudeResponse,
    ClaudeClient,
    ClaudeError,
)
from .mock import MockClaudeClient
from .live import LiveClaudeClient
from .factory import get_claude_client, set_claude_client, reset_claude_client

__all__ = [
    "ClaudeMessage",
    "ClaudeResponse",
    "ClaudeClient",
    "ClaudeError",
    "MockClaudeClient",
    "LiveClaudeClient",
    "get_claude_client",
    "set_claude_client",
    "reset_claude_client",
]
