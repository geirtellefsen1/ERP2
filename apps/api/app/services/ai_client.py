import httpx
import os


class ClaudeClient:
    def __init__(self):
        self.api_key = os.getenv("CLAUDE_API_KEY", "")
        self.base_url = "https://api.anthropic.com/v1"

    async def complete(
        self,
        system_prompt: str,
        user_message: str,
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 4096,
    ) -> str:
        """Send a message to the Claude API and return the response text.

        Returns a mock response if no API key is configured.
        """
        if not self.api_key:
            return f"[Mock AI Response] System: {system_prompt[:50]}... User: {user_message[:50]}..."

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": model,
                    "max_tokens": max_tokens,
                    "system": system_prompt,
                    "messages": [{"role": "user", "content": user_message}],
                },
                timeout=60.0,
            )
            response.raise_for_status()
            return response.json()["content"][0]["text"]
