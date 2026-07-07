# app/core/xeno.py
from typing import Optional, AsyncGenerator, List, Dict, Any
import asyncio
import logging
from app.config import settings
from app.core.prompts import build_system_prompt
from app.core.model_router import ModelRouter
from app.memory.memory_manager import MemoryManager
from app.rag.retriever import Retriever
from app.tools.registry import ToolRegistry
from app.database.repositories import MessageRepository
from app.chat.conversation import Message
from app.llm.ollama_client import OllamaClient
from app.llm.streaming import StreamProcessor

logger = logging.getLogger(__name__)

from app.core.intent_engine import IntentEngine
from app.core.response_validator import ResponseValidator
from app.llm.model_manager import ModelManager

class XENOCore:
    def __init__(self):
        self.ollama = OllamaClient()
        self.router = ModelRouter(self.ollama)
        self.intent_engine = IntentEngine()
        self.model_manager = ModelManager(self.ollama)
        self.validator = ResponseValidator()
        self.memory = MemoryManager()
        self.rag = Retriever() if settings.RAG_ENABLED else None
        self.tools = ToolRegistry()
        self.msg_repo = MessageRepository()
        self.stream_processor = StreamProcessor()

    async def chat_stream(
        self,
        conversation_id: str,
        user_message: str,
        model_name: Optional[str] = None,
        rag_enabled: Optional[bool] = None,
        long_term_enabled: Optional[bool] = None
    ) -> AsyncGenerator[str, None]:
        """
        Process a user message and yield streaming response chunks.
        """
        use_rag = settings.RAG_ENABLED if rag_enabled is None else rag_enabled
        use_long_term = settings.LONG_TERM_MEMORY_ENABLED if long_term_enabled is None else long_term_enabled

        # 1. Get conversation history (short-term memory)
        history = await self.memory.get_short_term(conversation_id, limit=settings.SHORT_TERM_MESSAGE_LIMIT)

        # 2. Retrieve long-term memory if enabled
        long_term = await self.memory.get_long_term(user_message) if use_long_term else []

        # 3. RAG retrieval
        rag_context = []
        if self.rag and use_rag:
            rag_context = await self.rag.retrieve(user_message, top_k=settings.RAG_TOP_K)

        # 4. Tool context (list available tools)
        tool_descriptions = self.tools.get_descriptions()

        # 5. Build system prompt
        system_prompt = build_system_prompt(
            long_term_memory=long_term,
            rag_context=rag_context,
            tool_descriptions=tool_descriptions
        )

        # 6. Prepare messages for Ollama
        messages = [
            {"role": "system", "content": system_prompt},
            *history,  # list of dicts with role/content
            {"role": "user", "content": user_message}
        ]

        # 7. Classify User Intent for Tools
        intent = await self.intent_engine.detect(user_message)
        if intent.requires_tool:
            logger.info(f"[XENO INTENT] Detected tool requirement: {intent.tool_name}")
            # Placeholder for tool execution if supported natively. For now continue routing.

        # 8. Determine model
        selected_model_or_role = model_name
        
        # If no model is explicitly passed or if it's default/None, use the router!
        if not selected_model_or_role or selected_model_or_role.lower() in ("default", "none"):
            if settings.XENO_ENABLE_MODEL_ROUTING:
                # Convert history models to raw dicts for router
                history_list = [{"role": m.get("role") if isinstance(m, dict) else m.role, 
                                 "content": m.get("content") if isinstance(m, dict) else m.content} 
                                for m in history]
                # Check for visual attachments (placeholder check for base64 or attachment triggers)
                has_image = "[image]" in user_message.lower() or "[screenshot]" in user_message.lower()
                
                route = self.router.route(user_message, history=history_list, has_image=has_image)
                selected_model_or_role = route.role.value
                logger.info(f"[XENO ROUTER] Role selected: {selected_model_or_role} (Confidence: {route.confidence:.2f}, Reason: {route.reason})")
            else:
                selected_model_or_role = settings.XENO_DEFAULT_MODEL_ROLE

        # 9. Save user message to DB
        self.msg_repo.create(conversation_id, "user", user_message)

        # 10. Call Ollama with streaming via the Model Manager (handles validation & fallbacks)
        try:
            async for token in self.model_manager.stream(selected_model_or_role, messages):
                # Sanitize identity leaks in real-time
                clean_token = self.validator.validate(token)
                yield clean_token
        except Exception as e:
            logger.exception("XENO Core streaming error")
            yield f"Error during model inference: {str(e)}"
            raise

    async def save_assistant_message(self, conversation_id: str, content: str):
        """Persist the complete assistant response."""
        self.msg_repo.create(conversation_id, "assistant", content)