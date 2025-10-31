# app/services/rag_client.py
import httpx
from app.config import settings

async def rag_query(query: str, k: int = 8, rerank: bool = True, timeout: int = None):
    timeout = timeout or settings.RAG_TIMEOUT
    url = f"{settings.RAG_SERVICE_URL.rstrip('/')}/query"
    payload = {"query": query, "k": k, "rerank": rerank}
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(url, json=payload)
        r.raise_for_status()
        return r.json()

async def rag_ingest(source: str, uri: str, metadata: dict = None, timeout: int = None):
    timeout = timeout or settings.RAG_TIMEOUT
    url = f"{settings.RAG_SERVICE_URL.rstrip('/')}/ingest"
    payload = {"source": source, "uri": uri, "metadata": metadata or {}}
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(url, json=payload)
        r.raise_for_status()
        return r.json()
