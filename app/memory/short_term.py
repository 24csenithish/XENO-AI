# app/memory/short_term.py
from app.database.repositories import MessageRepository
from typing import List, Dict

class ShortTermMemory:
    def __init__(self):
        self.repo = MessageRepository()

    async def get_recent_messages(self, conversation_id: str, limit: int) -> List[Dict[str, str]]:
        """Return list of messages in format [{role, content}]."""
        # Convert conversation_id to int (assuming it's stored as int)
        try:
            conv_id = int(conversation_id)
        except:
            conv_id = 0
        msgs = self.repo.get_messages(conv_id, limit=limit)
        return [{"role": m.role, "content": m.content} for m in msgs]