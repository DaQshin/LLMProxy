from .base import BaseProvider, ProviderResponse
from .rate_limiter import TokenBucket

class ProviderRouter:
    def __init__(self, providers: list[BaseProvider], rate_limits: dict[str, TokenBucket]):
        if not providers:
            raise ValueError("ProviderRouter rquires at least one router")
        
        self.providers = providers
        self.rate_limits = rate_limits

    
    async def generate(self, prompt: str, model: str, max_tokens: int) -> ProviderResponse:
        last_error: Exception | None = None

        for provider in self.providers:
            bucket = self.rate_limits.get(provider.name)
            if bucket and not await bucket.acquire():
                print(f"[router] {provider.name} rate-limited, trying next provider.")
                continue

            try:
                return await provider.generate(prompt=prompt, model=model, max_tokens=max_tokens)

            except RuntimeError as e:
                last_error = e
                print(f"[router] {provider.name} failed: {e}. Trying next provider.")
                continue

        raise RuntimeError(f"All providers failed. Last error: {last_error}")