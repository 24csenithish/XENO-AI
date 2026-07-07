# app/llm/model_detector.py
import logging
from typing import List, Dict, Optional
from app.llm.ollama_client import OllamaClient
from app.llm.model_registry import MODELS

logger = logging.getLogger(__name__)

class ModelDetector:
    def __init__(self, client: Optional[OllamaClient] = None):
        self.client = client or OllamaClient()

    async def get_installed_models(self) -> List[str]:
        """Fetch all installed models in Ollama."""
        return await self.client.list_models()

    async def is_model_installed(self, model_name: str) -> bool:
        """Check if a specific model is installed (case-insensitive check)."""
        return await self.client.model_exists(model_name)

    async def get_missing_models(self) -> Dict[str, str]:
        """Get dict of role: configured_model that are missing from the registry."""
        installed = await self.get_installed_models()
        installed_normalized = [m.lower() for m in installed]
        
        missing = {}
        for role, config in MODELS.items():
            model = config["model"]
            # Check if model or its prefix (base name without tags) is installed
            if not self._check_match(model, installed_normalized):
                missing[role] = model
        return missing

    async def find_compatible_model(self, role: str) -> Optional[str]:
        """
        Search for an installed model that might be compatible with the requested role.
        e.g. if qwen2.5vl:7b is missing but llava is installed, return llava.
        """
        installed = await self.get_installed_models()
        if not installed:
            return None

        config = MODELS.get(role)
        if not config:
            return None

        primary_model = config["model"].lower()
        base_primary = primary_model.split(":")[0]

        # 1. Exact or prefix match in installed list
        for m in installed:
            m_lower = m.lower()
            if base_primary in m_lower or m_lower.split(":")[0] in primary_model:
                return m

        # 2. Fallbacks by role type
        if role == "vision":
            vision_fallbacks = ["qwen2.5vl", "qwen3-vl", "llava", "minicpm-v", "vision"]
            for fallback in vision_fallbacks:
                for m in installed:
                    if fallback in m.lower():
                        return m
                        
        if role == "coding":
            coding_fallbacks = ["coder", "code", "qwen2.5-coder", "codellama"]
            for fallback in coding_fallbacks:
                for m in installed:
                    if fallback in m.lower():
                        return m

        if role == "reasoning":
            reasoning_fallbacks = ["r1", "deepseek-r1", "reasoning", "reason"]
            for fallback in reasoning_fallbacks:
                for m in installed:
                    if fallback in m.lower():
                        return m

        # If nothing matches, we can't recommend a role-specific compatibility model
        return None

    def _check_match(self, model_name: str, installed_list: List[str]) -> bool:
        normalized = model_name.lower()
        base_name = normalized.split(":")[0]
        for m in installed_list:
            if m == normalized or m.split(":")[0] == base_name:
                return True
        return False
