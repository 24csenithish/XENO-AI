# app/llm/providers.py
from typing import Dict, Type
from app.llm.base import BaseLLM
from app.llm.ollama_client import OllamaClient

PROVIDER_REGISTRY: Dict[str, Type[BaseLLM]] = {
    "ollama": OllamaClient,
}


def get_provider_client(provider: str, **kwargs) -> BaseLLM:
    """Instantiate an LLM provider client by name."""
    cls = PROVIDER_REGISTRY.get(provider)
    if cls is None:
        raise ValueError(f"Unknown LLM provider: '{provider}'")
    return cls(**kwargs)
