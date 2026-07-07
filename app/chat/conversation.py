# app/chat/conversation.py
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class Message(BaseModel):
    id: Optional[int] = None
    conversation_id: int
    role: str  # user, assistant, system, tool
    content: str
    created_at: datetime = datetime.utcnow()

class Conversation(BaseModel):
    id: Optional[int] = None
    title: str
    model: str
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()
    messages: List[Message] = []