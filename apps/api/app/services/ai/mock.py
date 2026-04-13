"""
MockClaudeClient — deterministic in-memory client for tests and dev.

Records every request so tests can assert against the prompt, system
instructions, model selection, and language directive. Returns a canned
response (configurable per instance or per test) so output is stable.
"""
from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Optional

from .base import ClaudeClient, ClaudeMessage, ClaudeResponse


@dataclass
class RecordedCall:
    """One call to MockClaudeClient.complete() captured for assertion."""
    system: str
    messages: list[ClaudeMessage]
    model: str
    max_tokens: int
    temperature: float
    language: Optional[str]


class MockClaudeClient(ClaudeClient):
    """In-memory Claude client. Use in tests and local dev without a key."""

    def __init__(
        self,
        canned_response: str = "This is a mock response.",
        canned_input_tokens: int = 100,
        canned_output_tokens: int = 50,
    ):
        self.canned_response = canned_response
        self.canned_input_tokens = canned_input_tokens
        self.canned_output_tokens = canned_output_tokens
        self._calls: list[RecordedCall] = []
        self._lock = threading.Lock()

    def complete(
        self,
        system: str,
        messages: list[ClaudeMessage],
        model: str = "claude-sonnet-4-6",
        max_tokens: int = 1024,
        temperature: float = 0.7,
        language: str | None = None,
    ) -> ClaudeResponse:
        # Mirror the language behaviour of LiveClaudeClient so tests can
        # assert that the directive made it into the system prompt.
        full_system = self._with_language(system, language)
        with self._lock:
            self._calls.append(
                RecordedCall(
                    system=full_system,
                    messages=list(messages),
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    language=language,
                )
            )
        return ClaudeResponse(
            text=self.canned_response,
            model=model,
            input_tokens=self.canned_input_tokens,
            output_tokens=self.canned_output_tokens,
            stop_reason="end_turn",
            raw={"mock": True},
        )

    @staticmethod
    def _with_language(system: str, language: str | None) -> str:
        if not language:
            return system
        return f"{system}\n\nRespond in {language}."

    # ── Test introspection ─────────────────────────────────────────

    @property
    def calls(self) -> list[RecordedCall]:
        with self._lock:
            return list(self._calls)

    def last_call(self) -> RecordedCall | None:
        with self._lock:
            return self._calls[-1] if self._calls else None

    def reset(self) -> None:
        with self._lock:
            self._calls.clear()
