from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, ScoredPoint
from sentence_transformers import SentenceTransformer
from .config import settings
from uuid import uuid4
from functools import partial
import asyncio 
import time

client = AsyncQdrantClient(host="localhost", port=6333)
encoder = SentenceTransformer("all-MiniLM-L6-v2")

COLLECTION_NAME="prompt_cache"
EMBEDDING_DIM=384

async def init_cache():
    collections = await client.get_collections()
    existing = [c.name for c in collections.collections]

    if COLLECTION_NAME not in existing:
        await client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE)
        )
        print(f"Collection created: {COLLECTION_NAME}")
    
    else:
        print(f"Collection already exists {COLLECTION_NAME}")


async def embed(text: str) -> list[float]:
    loop = asyncio.get_event_loop()
    vector = await loop.run_in_executor(None, partial(encoder.encode, text))
    return vector.tolist()

async def query_cache(text: str) -> tuple[list[ScoredPoint], float]:

    start = time.perf_counter()

    query_vector = await embed(text)
    results = await client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=1
    )

    latency_ms = (time.perf_counter() - start) * 1000

    return results, latency_ms

async def cache(prompt: str, response: str) -> None:
    vector = await embed(prompt)
    await client.upsert(
        collection_name=COLLECTION_NAME,
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
