from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
from .config import settings
from uuid import uuid4
import asyncio

client = QdrantClient(host="localhost", port=6333)
encoder = SentenceTransformer("all-MiniLM-L6-v2")

COLLECTION_NAME="prompt_cache"
EMBEDDING_DIM=384

def init_cache():
    print(client.get_collections())
    existing = [c.name for c in client.get_collections().collections]

    if COLLECTION_NAME not in existing:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectorConfig=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE)
        )
        print(f"Collection created: {COLLECTION_NAME}")
    
    else:
        print(f"Collection already exists {COLLECTION_NAME}")


def embed(text: str) -> list[float]:
    return encoder.encode(text).tolist()

def query_cache(text: str) -> str | None:
    query_vector = embed(text)
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=1
    )

    return results

def cache(prompt: str, response: str) -> None:
    vector = embed(prompt)
    client.upsert(
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
