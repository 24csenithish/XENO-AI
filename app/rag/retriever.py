# app/rag/retriever.py
import asyncio
import logging
import os
from typing import List
from app.rag.loader import DocumentLoader
from app.rag.embeddings import EmbeddingGenerator
from app.rag.vector_store import VectorStore

logger = logging.getLogger(__name__)

class Retriever:
    def __init__(self):
        self.loader = DocumentLoader()
        self.embedder = EmbeddingGenerator()
        self.store = VectorStore()
        self._load_all_documents()

    def _load_all_documents(self):
        knowledge_dir = "data/knowledge"
        if not os.path.exists(knowledge_dir):
            os.makedirs(knowledge_dir, exist_ok=True)
            return

        try:
            asyncio.get_running_loop()
            logger.warning("Skipping RAG document preload inside a running event loop")
            return
        except RuntimeError:
            pass

        for fname in os.listdir(knowledge_dir):
            file_path = os.path.join(knowledge_dir, fname)
            if os.path.isfile(file_path):
                try:
                    text = self.loader.load(file_path)
                    chunks = [c.strip() for c in text.split("\n\n") if c.strip()]
                    for chunk in chunks:
                        embedding = asyncio.run(self.embedder.embed(chunk))
                        self.store.add(chunk, embedding)
                except Exception as e:
                    logger.warning("Failed to load %s: %s", fname, e)

    async def retrieve(self, query: str, top_k: int) -> List[str]:
        try:
            embedding = await self.embedder.embed(query)
        except Exception as e:
            logger.warning("RAG retrieval disabled for this request: %s", e)
            return []

        return self.store.search(embedding, top_k)