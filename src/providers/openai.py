import httpx
from .base import BaseProvider, ProviderResponse
from ..config import settings

class OpenAIProvider(BaseProvider):
    name = "openai"

    async def generate(self, prompt: str, model: str, max_tokens: int) -> ProviderResponse:
        async with httpx.AsyncClient() as client:
            res = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.openai_api_key}",
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
            raise RuntimeError(f"OpenAI API error: {res.status_code} {res.text}")

        data = res.json()
        return ProviderResponse(
            text=data["choices"][0]["message"]["content"],
            input_tokens=data["usage"]["prompt_tokens"],
            output_tokens=data["usage"]["completion_tokens"],
            model=model
        )