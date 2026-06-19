from langcache import LangCache
import asyncio
from .config import settings

class SemanticCache:

    def __init__(self):
        self.cache = None

    async def init_cache(self):
        self.cache = LangCache(
            "https://aws-ap-south-1.langcache.redis.io",
            cache_id=settings.langcache_id,
            api_key=settings.langcache_api
        )

        await self.cache.__aenter__()

    async def close(self):
        await self.cache.__aexit__(None, None, None)

    async def set(self, prompt: str, response: str):
        return await self.cache.set_async(prompt=prompt, response=response)


    async def get(self, prompt: str):
        result = await self.cache.search_async(prompt=prompt)

        if result is not None:
            if result.data is not None and len(result.data) > 0:
                return result.data[0].response
            
        return None
    
semantic_cache = SemanticCache()
    
