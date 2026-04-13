"""
Factory for the active Claude client.

Lets tests inject a MockClaudeClient via set_claude_client() and lets
production code call get_claude_client() without knowing whether the
backend is real or mocked.
"""
from __future__ import annotations

import threading
from typing import Optional

from .base import ClaudeClient
from .mock import MockClaudeClient
from .live import LiveClaudeClient


_lock = threading.Lock()
_override: Optional[ClaudeClient] = None


def get_claude_client() -> ClaudeClient:
    """
    Return the active Claude client. If a test has injected an override,
    return that. Otherwise try to construct a LiveClaudeClient — if that
    fails (no real API key set, e.g. in tests) fall back to a default
    MockClaudeClient so importing this module never crashes the test
    suite.
    """
    global _override
    with _lock:
        if _override is not None:
            return _override
        try:
            return LiveClaudeClient()
        except Exception:
            # No real key — fall back to a default mock so the import
            # works in test/dev environments without an explicit override.
            return MockClaudeClient(
                canned_response="(mock — no CLAUDE_API_KEY set)"
            )


def set_claude_client(client: ClaudeClient) -> None:
    """Inject a specific client. Tests use this to install a MockClaudeClient."""
    global _override
    with _lock:
        _override = client


def reset_claude_client() -> None:
    """Clear the override so get_claude_client() reverts to autodetection."""
    global _override
    with _lock:
        _override = None
