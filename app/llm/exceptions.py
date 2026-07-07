# app/llm/exceptions.py
from app.core.exceptions import XENOError, ModelNotFoundError, OllamaConnectionError

class ModelExecutionError(XENOError):
    """Raised when local LLM generation or streaming fails."""
    pass

class FallbackUnavailableError(XENOError):
    """Raised when fallback models are configured but none are available locally."""
    pass
