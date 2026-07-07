# app/rag/vector_store.py
from typing import List, Tuple
import numpy as np

class VectorStore:
    def __init__(self):
        self.chunks = []  # list of (text, embedding)

    def add(self, text: str, embedding: List[float]):
        self.chunks.append((text, np.array(embedding)))

    def search(self, query_embedding: List[float], top_k: int) -> List[str]:
        if not self.chunks:
            return []
        q = np.array(query_embedding)
        scores = []
        for text, emb in self.chunks:
            sim = np.dot(q, emb) / (np.linalg.norm(q) * np.linalg.norm(emb))
            scores.append((sim, text))
        scores.sort(reverse=True, key=lambda x: x[0])
        return [text for _, text in scores[:top_k]]