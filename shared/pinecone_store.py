"""Pinecone vector store for personalization with in-memory fallback."""

import hashlib
import json
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger("travelsouls.pinecone")

_memory_vectors: Dict[str, Dict[str, Any]] = {}
_index: Any = None
_index_ready: Optional[bool] = None


def _simple_embedding(text: str, dim: int = 128) -> List[float]:
    """Deterministic pseudo-embedding when OpenAI embeddings unavailable."""
    digest = hashlib.sha256(text.encode()).digest()
    return [digest[i % len(digest)] / 255.0 for i in range(dim)]


async def get_embedding(text: str) -> List[float]:
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://api.openai.com/v1/embeddings",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={"input": text, "model": "text-embedding-3-small"},
                    timeout=10.0,
                )
                if resp.status_code == 200:
                    return resp.json()["data"][0]["embedding"]
        except Exception as exc:
            logger.warning("OpenAI embedding failed: %s", exc)
    return _simple_embedding(text)


def _get_index():
    global _index, _index_ready
    if _index_ready is False:
        return None
    if _index is not None:
        return _index
    api_key = os.getenv("PINECONE_API_KEY")
    index_name = os.getenv("PINECONE_INDEX_NAME", "travelsouls")
    if not api_key:
        _index_ready = False
        return None
    try:
        from pinecone import Pinecone
        pc = Pinecone(api_key=api_key)
        if index_name not in [i.name for i in pc.list_indexes()]:
            pc.create_index(name=index_name, dimension=1536, metric="cosine", spec={"serverless": {"cloud": "aws", "region": "us-east-1"}})
        _index = pc.Index(index_name)
        _index_ready = True
        logger.info("Pinecone index connected: %s", index_name)
        return _index
    except Exception as exc:
        _index_ready = False
        logger.warning("Pinecone unavailable, using in-memory store: %s", exc)
        return None


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


async def upsert_preference(user_id: int, preferences: Dict[str, Any]) -> None:
    text = json.dumps(preferences, sort_keys=True)
    vector = await get_embedding(text)
    vector_id = f"user-{user_id}"
    metadata = {"user_id": user_id, **preferences}
    index = _get_index()
    if index:
        try:
            index.upsert(vectors=[{"id": vector_id, "values": vector, "metadata": metadata}])
            return
        except Exception as exc:
            logger.warning("Pinecone upsert failed: %s", exc)
    _memory_vectors[vector_id] = {"vector": vector, "metadata": metadata}


async def upsert_feedback(user_id: int, item_id: str, rating: int, item_type: str) -> None:
    text = f"user:{user_id} item:{item_id} type:{item_type} rating:{rating}"
    vector = await get_embedding(text)
    vector_id = f"feedback-{user_id}-{item_id}"
    metadata = {"user_id": user_id, "item_id": item_id, "rating": rating, "item_type": item_type}
    index = _get_index()
    if index:
        try:
            index.upsert(vectors=[{"id": vector_id, "values": vector, "metadata": metadata}])
            return
        except Exception as exc:
            logger.warning("Pinecone feedback upsert failed: %s", exc)
    _memory_vectors[vector_id] = {"vector": vector, "metadata": metadata}


async def query_similar_preferences(destination: str, travel_style: str, top_k: int = 5) -> List[Dict[str, Any]]:
    query_text = f"destination:{destination} style:{travel_style}"
    vector = await get_embedding(query_text)
    index = _get_index()
    if index:
        try:
            results = index.query(vector=vector, top_k=top_k, include_metadata=True)
            return [m.metadata for m in results.get("matches", []) if m.metadata]
        except Exception as exc:
            logger.warning("Pinecone query failed: %s", exc)
    scored = []
    for entry in _memory_vectors.values():
        sim = _cosine_similarity(vector, entry["vector"])
        scored.append((sim, entry["metadata"]))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [m for _, m in scored[:top_k]]
