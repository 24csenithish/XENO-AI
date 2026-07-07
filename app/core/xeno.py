# app/core/xeno.py
from typing import Optional, AsyncGenerator, List, Dict, Any
import logging

from app.config import settings
from app.core.prompts import build_system_prompt
from app.core.model_router import ModelRouter
from app.memory.memory_manager import MemoryManager
from app.rag.retriever import Retriever
from app.tools.registry import ToolRegistry
from app.tools.system_info import system_info
from app.tools.python_tool import execute_python
from app.database.repositories import MessageRepository
from app.llm.ollama_client import OllamaClient
from app.core.intent_engine import IntentEngine
from app.core.response_validator import ResponseValidator
from app.llm.model_manager import ModelManager
from app.llm.exceptions import FallbackUnavailableError, ModelExecutionError, OllamaConnectionError
from app.models.schemas import RoutingResult

logger = logging.getLogger(__name__)


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
        self.last_route: Optional[RoutingResult] = None
        self.last_resolved_model: Optional[str] = None
        self._register_tools()

    def _register_tools(self) -> None:
        if settings.ENABLE_SYSTEM_INFO_TOOL:
            self.tools.register(
                "system_info",
                system_info,
                "Get system information (OS, CPU, RAM, GPU).",
            )
        if settings.ENABLE_PYTHON_TOOL:
            self.tools.register(
                "python_exec",
                execute_python,
                "Execute Python code in a sandboxed environment.",
            )

    async def chat_stream(
        self,
        conversation_id: str,
        user_message: str,
        model_name: Optional[str] = None,
        rag_enabled: Optional[bool] = None,
        long_term_enabled: Optional[bool] = None,
        has_image: bool = False,
    ) -> AsyncGenerator[str, None]:
        """Process a user message and yield streaming response chunks."""
        use_rag = settings.RAG_ENABLED if rag_enabled is None else rag_enabled
        use_long_term = (
            settings.LONG_TERM_MEMORY_ENABLED if long_term_enabled is None else long_term_enabled
        )

        history_limit = min(
            settings.SHORT_TERM_MESSAGE_LIMIT,
            settings.XENO_MAX_HISTORY_MESSAGES,
        )
        history = await self.memory.get_short_term(conversation_id, limit=history_limit)
        long_term = await self.memory.get_long_term(user_message) if use_long_term else []

        rag_context = []
        if self.rag and use_rag:
            rag_context = await self.rag.retrieve(user_message, top_k=settings.RAG_TOP_K)

        tool_descriptions = self.tools.get_descriptions()

        intent = await self.intent_engine.detect(user_message)
        if intent.requires_tool and intent.tool_name:
            logger.info("[XENO INTENT] Detected tool requirement: %s", intent.tool_name)
            try:
                tool_result = await self.tools.execute(intent.tool_name)
                yield f"**Tool Result ({intent.tool_name}):**\n```\n{tool_result}\n```\n"
                return
            except Exception as e:
                logger.exception("[XENO INTENT] Tool execution failed")
                yield f"XENO tool execution failed: {e}"
                return

        selected_role: Optional[str] = None
        selected_model_or_role = model_name

        if not selected_model_or_role or selected_model_or_role.lower() in (
            "default", "none", "auto",
        ):
            if settings.XENO_ENABLE_MODEL_ROUTING:
                history_list = [
                    {
                        "role": m.get("role") if isinstance(m, dict) else m.role,
                        "content": m.get("content") if isinstance(m, dict) else m.content,
                    }
                    for m in history
                ]
                image_detected = (
                    has_image
                    or "[image]" in user_message.lower()
                    or "[screenshot]" in user_message.lower()
                )
                route = self.router.route(
                    user_message,
                    history=history_list,
                    has_image=image_detected,
                )
                self.last_route = route
                selected_role = route.role.value
                selected_model_or_role = selected_role
                logger.info("[XENO ROUTER] Role selected: %s", selected_role)
                logger.info("[XENO ROUTER] Confidence: %.2f", route.confidence)
                logger.info("[XENO ROUTER] Reason: %s", route.reason)
            else:
                selected_model_or_role = settings.XENO_DEFAULT_MODEL_ROLE
                selected_role = selected_model_or_role

        if selected_role == "vision" or (
            selected_model_or_role == "vision"
        ):
            status = await self.model_manager.get_model_status()
            if status.get("vision") == "MISSING":
                yield (
                    "XENO image analysis requires a local vision model. "
                    "Install one with: `ollama pull qwen2.5vl:7b` "
                    "(or llava, minicpm-v as alternatives)."
                )
                return

        system_prompt = build_system_prompt(
            long_term_memory=long_term,
            rag_context=rag_context,
            tool_descriptions=tool_descriptions,
            role=selected_role or (
                selected_model_or_role
                if selected_model_or_role in self.model_manager.get_available_roles()
                else None
            ),
        )

        messages = [
            {"role": "system", "content": system_prompt},
            *history,
            {"role": "user", "content": user_message},
        ]

        self.msg_repo.create(conversation_id, "user", user_message)

        full_response = ""
        try:
            async for token in self.model_manager.stream(selected_model_or_role, messages):
                clean_token = self.validator.validate_stream_chunk(token)
                full_response += clean_token
                yield clean_token

            self.last_resolved_model = self.model_manager.get_active_model()
            if not full_response.strip():
                yield self.validator.validate(full_response)

        except OllamaConnectionError:
            logger.exception("[XENO] Ollama connection error")
            yield "XENO local AI engine is offline. Start Ollama and try again."
        except FallbackUnavailableError as e:
            logger.error("[XENO] No models available: %s", e)
            yield str(e)
        except ModelExecutionError as e:
            logger.exception("[XENO] Model execution error")
            role = selected_model_or_role
            yield (
                f"XENO model execution failed for role '{role}'. "
                f"The system attempted fallback models. Error: {e}"
            )
        except Exception as e:
            logger.exception("[XENO] Unexpected streaming error")
            yield f"XENO encountered an unexpected error. Please try again."

    async def save_assistant_message(self, conversation_id: str, content: str) -> None:
        """Persist the complete assistant response."""
        self.msg_repo.create(conversation_id, "assistant", content)

    def get_last_engine_info(self) -> Dict[str, Any]:
        """Return routing/engine info for frontend display."""
        info: Dict[str, Any] = {
            "role": None,
            "model": self.last_resolved_model or self.model_manager.get_active_model(),
            "confidence": None,
            "provider": "ollama",
        }
        if self.last_route:
            info["role"] = self.last_route.role.value
            info["confidence"] = self.last_route.confidence
        elif self.model_manager.get_active_role():
            info["role"] = self.model_manager.get_active_role()
        return info
