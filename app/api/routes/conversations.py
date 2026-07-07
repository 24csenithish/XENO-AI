# app/api/routes/conversations.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.chat.chat_manager import ChatManager
from app.chat.conversation import Conversation

router = APIRouter()
chat_mgr = ChatManager()

class CreateConversationRequest(BaseModel):
    model: Optional[str] = None

class UpdateConversationRequest(BaseModel):
    title: str

@router.get("/", response_model=List[Conversation])
async def list_conversations():
    return await chat_mgr.list_conversations()

@router.post("/", response_model=Conversation)
async def create_conversation(req: CreateConversationRequest):
    return await chat_mgr.create_conversation(req.model)

@router.get("/{conv_id}", response_model=Conversation)
async def get_conversation(conv_id: int):
    conv = await chat_mgr.get_conversation(conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv

@router.patch("/{conv_id}")
async def update_conversation(conv_id: int, req: UpdateConversationRequest):
    await chat_mgr.rename_conversation(conv_id, req.title)
    return {"status": "ok"}

@router.delete("/{conv_id}")
async def delete_conversation(conv_id: int):
    await chat_mgr.delete_conversation(conv_id)
    return {"status": "ok"}