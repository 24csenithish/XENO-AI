# app/chat/chat_manager.py
from app.database.repositories import ConversationRepository, MessageRepository
from app.chat.conversation import Conversation, Message
from app.core.xeno import XENOCore
from typing import AsyncGenerator, List, Optional



class ChatManager:
    def __init__(self):
        self.conv_repo = ConversationRepository()
        self.msg_repo = MessageRepository()
        self.xeno = XENOCore()

    async def create_conversation(self, model: Optional[str] = None) -> Conversation:
        """Create a new conversation with default title and model."""
        conv = Conversation(
            title="New Chat",
            model=model or "default",
        )
        return self.conv_repo.create(conv)

    async def get_conversation(self, conv_id: int) -> Conversation:
        return self.conv_repo.get(conv_id)

    async def list_conversations(self) -> List[Conversation]:
        return self.conv_repo.list()

    async def get_messages(self, conv_id: int):
        return self.msg_repo.get_messages(conv_id)

    async def delete_conversation(self, conv_id: int):
        self.conv_repo.delete(conv_id)

    async def rename_conversation(self, conv_id: int, new_title: str):
        self.conv_repo.update_title(conv_id, new_title)

    async def send_message(
        self,
        conv_id: int,
        user_message: str,
        model: Optional[str] = None,
        rag_enabled: Optional[bool] = None,
        long_term_enabled: Optional[bool] = None
    ) -> AsyncGenerator[str, None]:
        """Send a user message and stream assistant response."""
        # Ensure conversation exists
        conv = self.conv_repo.get(conv_id)
        if not conv:
            raise ValueError("Conversation not found")

        # If conversation title is "New Chat", generate title from first user message
        if conv.title == "New Chat":
            new_title = self._generate_title(user_message)
            self.conv_repo.update_title(conv_id, new_title)

        # Stream the response from XENOCore
        async for chunk in self.xeno.chat_stream(
            str(conv_id), user_message, model, rag_enabled, long_term_enabled
        ):
            yield chunk

        # After streaming, we need to save the assistant response.
        # The XENOCore doesn't accumulate; we need to capture full response in frontend/API.
        # For simplicity, we'll handle saving in the caller (frontend/API) by passing the complete response.
        # However, to keep the manager responsible, we can have a separate method to save assistant message.
        # We'll implement it in the caller.

    async def save_assistant_message(self, conv_id: int, content: str):
        self.msg_repo.create(conv_id, "assistant", content)

    def _generate_title(self, text: str) -> str:
        """Generate a concise title from the first user message."""
        # Simple truncation
        if len(text) > 40:
            return text[:40] + "..."
        return text