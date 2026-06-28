from .base import BaseProvider, ProviderResponse
from ..rate_limiter import TokenBucket
import structlog

logger = structlog.get_logger()

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
                logger.warning("provider_rate_limited", provider=provider.name)
                continue

            try:
                result = await provider.generate(prompt=prompt, model=model, max_tokens=max_tokens)
                logger.info("provider_success", provider=provider.name, model=model)
                return result
            
            except RuntimeError as e:
                last_error = e
                logger.warning("provider_error", provider=provider.name, error=str(e))
                continue

        raise RuntimeError(f"All providers failed. Last error: {last_error}")