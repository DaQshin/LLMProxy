import httpx
from .base import BaseProvider, ProviderResponse
from ..config import settings

class ClaudeProvider(BaseProvider):
    name = "claude"

    async def generate(self, prompt: str, model: str, max_tokens: int) -> ProviderResponse:
        async with httpx.AsyncClient() as client:
            res = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": settings.anthropic_api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": model,
                    "max_tokens": max_tokens,
                    "messages": [{"role": "user", "content": prompt}]
                },
                timeout=30.0
            )

        if res.status_code != 200:
            raise RuntimeError(f"Claude API error: {res.status_code} {res.text}")

        data = res.json()
        return ProviderResponse(
            text=data["content"][0]["text"],
            input_tokens=data["usage"]["input_tokens"],
            output_tokens=data["usage"]["output_tokens"],
            model=model
        )