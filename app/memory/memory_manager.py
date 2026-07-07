# app/memory/memory_manager.py
from app.memory.short_term import ShortTermMemory
from app.memory.long_term import LongTermMemory

class MemoryManager:
    def __init__(self):
        self.short = ShortTermMemory()
        self.long = LongTermMemory()

    async def get_short_term(self, conversation_id: str, limit: int):
        return await self.short.get_recent_messages(conversation_id, limit)

    async def get_long_term(self, query: str):
        return await self.long.retrieve(query)