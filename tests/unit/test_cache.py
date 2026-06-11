from unittest import IsolatedAsyncioTestCase
from src.cache import SemanticCache
import asyncio
from src.config import settings

class TestCache(IsolatedAsyncioTestCase):

    @classmethod
    def setUpClass(cls):
        cls.cache = SemanticCache(
            host=settings.qdrant_host, 
            port=settings.qdrant_port, 
            collection="test_collection"
            )
        
    async def asyncSetUp(self):
        await self.cache.init_cache()

    async def asyncTearDown(cls):
        await cls.cache.clear_cache()
    
    async def test_cache_miss(self):
        sample_prompt = "What is FastAPI?"
        result, _ = await self.cache.get(sample_prompt)

        assert result is None

    async def test_cache_hit(self):
        await self.cache.set(
        prompt="What is FastAPI?",
        response="A Python web framework"
        )

        result, _ = await self.cache.get("What is FastAPI?")

        assert result['response'] == "A Python web framework"

    async def test_similar_prompts(self):

        await self.cache.set(
        prompt="What is FastAPI?",
        response="A Python web framework"
        )
        
        result, _ = await self.cache.get("I don't what FastAPI is.")

        assert result['response'] == "A Python web framework"

    