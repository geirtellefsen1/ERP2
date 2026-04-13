"""
LiveClaudeClient — talks to the real Anthropic API via httpx.

Production-grade: retries on transient errors, structured logging, no
secret leakage in error messages. The API key is read from settings,
never passed in the request URL or logged.
"""
from __future__ import annotations

import logging
import time
from typing import Optional

import httpx

from app.config import get_settings

from .base import ClaudeClient, ClaudeError, ClaudeMessage, ClaudeResponse

logger = logging.getLogger(__name__)

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"

LANGUAGE_DIRECTIVES = {
    "nb-NO": "Respond in Norwegian Bokmål (nb-NO). All output must be in Norwegian.",
    "sv-SE": "Respond in Swedish (sv-SE). All output must be in Swedish.",
    "fi-FI": "Respond in Finnish (fi-FI). All output must be in Finnish.",
    "en": "Respond in English. All output must be in English.",
    "en-GB": "Respond in British English. All output must be in English.",
    "en-US": "Respond in American English. All output must be in English.",
}


class LiveClaudeClient(ClaudeClient):
    """Real Claude API client. Use only when CLAUDE_API_KEY is set."""

    def __init__(self, api_key: Optional[str] = None, timeout: float = 60.0):
        self.api_key = api_key or get_settings().claude_api_key
        if not self.api_key or self.api_key.startswith("sk-ant-test"):
            # Test placeholder key — refuse to make real network calls.
            # Use MockClaudeClient in tests instead.
            raise ClaudeError(
                "LiveClaudeClient requires a real CLAUDE_API_KEY. "
                "For tests, use MockClaudeClient."
            )
        self.timeout = timeout

    def complete(
        self,
        system: str,
        messages: list[ClaudeMessage],
        model: str = "claude-sonnet-4-6",
        max_tokens: int = 1024,
        temperature: float = 0.7,
        language: str | None = None,
    ) -> ClaudeResponse:
        full_system = self._with_language(system, language)
        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": full_system,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
        }
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        }

        # Simple retry on transient errors only
        last_error = None
        for attempt in range(3):
            try:
                with httpx.Client(timeout=self.timeout) as http:
                    resp = http.post(ANTHROPIC_URL, json=payload, headers=headers)
                if resp.status_code == 200:
                    return self._parse(resp.json())
                if resp.status_code in (429, 500, 502, 503, 504):
                    last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
                    logger.warning(
                        "Claude API transient error (attempt %d): %s",
                        attempt + 1,
                        resp.status_code,
                    )
                    time.sleep(2 ** attempt)
                    continue
                # Non-retryable
                raise ClaudeError(f"Claude API error {resp.status_code}: {resp.text[:200]}")
            except httpx.RequestError as e:
                last_error = str(e)
                logger.warning("Claude API network error (attempt %d): %s", attempt + 1, e)
                time.sleep(2 ** attempt)

        raise ClaudeError(f"Claude API failed after retries: {last_error}")

    @staticmethod
    def _with_language(system: str, language: str | None) -> str:
        if not language:
            return system
        directive = LANGUAGE_DIRECTIVES.get(language)
        if not directive:
            return system
        return f"{system}\n\n{directive}"

    @staticmethod
    def _parse(body: dict) -> ClaudeResponse:
        try:
            content_blocks = body.get("content", [])
            text_parts = [b.get("text", "") for b in content_blocks if b.get("type") == "text"]
            usage = body.get("usage", {})
            return ClaudeResponse(
                text="".join(text_parts),
                model=body.get("model", "unknown"),
                input_tokens=usage.get("input_tokens", 0),
                output_tokens=usage.get("output_tokens", 0),
                stop_reason=body.get("stop_reason", "end_turn"),
                raw=body,
            )
        except Exception as e:
            raise ClaudeError(f"Failed to parse Claude response: {e}") from e
