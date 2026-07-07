# app/llm/base.py
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, Any, List, Optional

class BaseLLM(ABC):
    """Abstract base class representing a local LLM inference provider."""

    @abstractmethod
    async def generate(
        self, 
        model: str, 
        messages: List[Dict[str, str]], 
        options: Optional[Dict[str, Any]] = None,
        keep_alive: Optional[str] = None
    ) -> str:
        """Generate a complete response synchronously (non-streaming)."""
        pass

    @abstractmethod
    async def stream_chat(
        self, 
        model: str, 
        messages: List[Dict[str, str]], 
        options: Optional[Dict[str, Any]] = None,
        keep_alive: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream response chunks asynchronously."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the inference service/backend is online."""
        pass

    @abstractmethod
    async def list_models(self) -> List[str]:
        """List all available models loaded in the backend."""
        pass

    @abstractmethod
    async def model_exists(self, model_name: str) -> bool:
        """Check if a specific model exists in the backend."""
        pass
