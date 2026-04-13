"""Abstract Claude client interface and value objects."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Literal, Optional


Role = Literal["user", "assistant"]


@dataclass
class ClaudeMessage:
    role: Role
    content: str


@dataclass
class ClaudeResponse:
    text: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    stop_reason: str = "end_turn"
    raw: Optional[dict] = None


class ClaudeError(Exception):
    """Raised on any Claude API failure (HTTP, parsing, rate limits)."""


class ClaudeClient(ABC):
    """Interface every Claude client implementation must honour."""

    @abstractmethod
    def complete(
        self,
        system: str,
        messages: list[ClaudeMessage],
        model: str = "claude-sonnet-4-6",
        max_tokens: int = 1024,
        temperature: float = 0.7,
        language: str | None = None,
    ) -> ClaudeResponse:
        """
        Send a completion request to Claude.

        Args:
            system: System prompt with the model's role and instructions.
            messages: User/assistant turn history.
            model: Anthropic model ID.
            max_tokens: Cap on the response length.
            temperature: Sampling temperature 0.0-1.0.
            language: IETF locale tag (nb-NO, sv-SE, fi-FI, en).
                If set, the wrapper appends a language directive to the
                system prompt so output comes back in the right language.
        """
