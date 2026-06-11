from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, ScoredPoint
from sentence_transformers import SentenceTransformer
from .config import settings
from uuid import uuid4
import asyncio 
import time

class SemanticCache:

    encoder_model = SentenceTransformer("all-MiniLM-L6-v2")

    def __init__(self, 
                host: str, 
                port: int, 
                collection: str = "prompt_cache",
                embedding_dim: int = 384
                ):
        self._client = AsyncQdrantClient(host=host, port=port)
        self.collection = collection
        self.embedding_dim = embedding_dim

    
    async def init_cache(self):
        collections = await self._client.get_collections()
        existing = [c.name for c in collections.collections]

        if self.collection not in existing:
            await self._client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(size=self.embedding_dim, distance=Distance.COSINE)
            )

            print(f"Collection created: {self.collection}")

        else:
            print(f"Collection already exists.")

    async def embed(self, text: str) -> list[float]:
        loop = asyncio.get_running_loop()
        vector = await loop.run_in_executor(None, self.encoder_model.encode, text)
        return vector.tolist()
    
    async def get(self, text: str) -> tuple[list[ScoredPoint], float]:
        
        start = time.perf_counter()

        query_vector = await self.embed(text)
        result = await self._client.query_points(
            collection_name=self.collection,
            query=query_vector,
            limit=1
        )

        latency_ms = (time.perf_counter() - start) * 1000

        if result is not None:
            if result.points is not None and len(result.points) > 0:
                return result.points[0].payload, latency_ms
            
        return None, latency_ms
    
    async def set(self, prompt: str, response: str) -> None:
        vector = await self.embed(prompt)
        await self._client.upsert(
            collection_name=self.collection,
            points=[
                PointStruct(
                    id=str(uuid4()),
                    vector=vector,
                    payload={
                        "prompt": prompt,
                        "response": response
                    }
                )   
            ]
        )

    async def clear_cache(self) -> None:
        await self._client.delete_collection(
            collection_name=self.collection
        )


cache = SemanticCache(
    host=settings.qdrant_host, 
    port=settings.qdrant_port 
    )