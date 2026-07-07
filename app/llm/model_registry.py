# app/llm/model_registry.py
from typing import Dict, Any, Optional
from app.models.schemas import ModelRole

# The Registry is the single source of truth for model role configurations.
MODELS: Dict[str, Dict[str, Any]] = {
    ModelRole.GENERAL.value: {
        "model": "qwen3:8b",  # Will fallback to settings config if needed
        "provider": "ollama",
        "priority": 1,
        "fallback": ModelRole.FAST.value,
        "keep_alive": "5m",
        "options": {
            "temperature": 0.7,
            "top_p": 0.9,
            "num_ctx": 4096,
        }
    },
    ModelRole.CODING.value: {
        "model": "qwen2.5-coder:7b",
        "provider": "ollama",
        "priority": 1,
        "fallback": ModelRole.GENERAL.value,
        "keep_alive": "3m",
        "options": {
            "temperature": 0.2,
            "top_p": 0.95,
            "num_ctx": 8192,
        }
    },
    ModelRole.REASONING.value: {
        "model": "deepseek-r1:8b",
        "provider": "ollama",
        "priority": 1,
        "fallback": ModelRole.GENERAL.value,
        "keep_alive": "1m",
        "options": {
            "temperature": 0.6,
            "top_p": 0.9,
            "num_ctx": 8192,
        }
    },
    ModelRole.FAST.value: {
        "model": "llama3.2:3b",
        "provider": "ollama",
        "priority": 1,
        "fallback": ModelRole.GENERAL.value,
        "keep_alive": "10m",
        "options": {
            "temperature": 0.5,
            "top_p": 0.9,
            "num_ctx": 2048,
        }
    },
    ModelRole.VISION.value: {
        "model": "qwen2.5vl:7b",
        "provider": "ollama",
        "priority": 1,
        "fallback": ModelRole.GENERAL.value,
        "keep_alive": "1m",
        "options": {
            "temperature": 0.4,
            "top_p": 0.9,
            "num_ctx": 4096,
        }
    }
}

def get_role_config(role: str) -> Optional[Dict[str, Any]]:
    """Retrieve model registry configuration for a specific role."""
    return MODELS.get(role)
