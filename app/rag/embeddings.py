# app/rag/embeddings.py
from typing import List
import aiohttp
from app.config import settings

class EmbeddingGenerator:
    def __init__(self):
        self.host = settings.OLLAMA_HOST
        self.model = settings.RAG_EMBEDDING_MODEL

    async def embed(self, text: str) -> List[float]:
        url = f"{self.host}/api/embeddings"
        payload = {"model": self.model, "prompt": text}
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("embedding", [])
                else:
                    raise Exception(f"Embedding failed: {await resp.text()}")