# tests/test_chat.py
import pytest
from app.chat.chat_manager import ChatManager

@pytest.mark.asyncio
async def test_create_conversation():
    mgr = ChatManager()
    conv = await mgr.create_conversation()
    assert conv.id is not None
    assert conv.title == "New Chat"