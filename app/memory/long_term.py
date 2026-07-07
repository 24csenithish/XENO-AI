# app/memory/long_term.py
from typing import List
from app.database.models import Memory
from app.database.database import SessionLocal

class LongTermMemory:
    def __init__(self):
        pass

    async def store(self, content: str, memory_type: str = "general", importance: int = 1):
        db = SessionLocal()
        try:
            mem = Memory(content=content, memory_type=memory_type, importance=importance)
            db.add(mem)
            db.commit()
        finally:
            db.close()

    async def retrieve(self, query: str, top_k: int = 5) -> List[dict]:
        db = SessionLocal()
        try:
            memories = db.query(Memory).order_by(Memory.importance.desc(), Memory.created_at.desc()).limit(top_k).all()
            return [{"content": m.content, "importance": m.importance} for m in memories]
        finally:
            db.close()