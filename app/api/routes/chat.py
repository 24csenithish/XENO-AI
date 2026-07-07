# app/api/routes/chat.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from app.chat.chat_manager import ChatManager

router = APIRouter()
chat_mgr = ChatManager()

class ChatRequest(BaseModel):
    conversation_id: int
    message: str
    model: Optional[str] = None

@router.post("/")
async def chat(request: ChatRequest):
    # Non-streaming (not used by frontend, but can be provided)
    # We'll implement streaming endpoint
    pass

@router.post("/stream")
async def chat_stream(request: ChatRequest):
    async def generate():
        async for chunk in chat_mgr.send_message(request.conversation_id, request.message, request.model):
            yield chunk
    return StreamingResponse(generate(), media_type="text/plain")