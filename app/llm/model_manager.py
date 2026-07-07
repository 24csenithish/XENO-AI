# app/llm/model_manager.py
import logging
from typing import AsyncGenerator, Dict, Any, List, Optional
from app.llm.ollama_client import OllamaClient
from app.llm.model_detector import ModelDetector
from app.llm.model_registry import MODELS, get_role_config
from app.models.schemas import ModelRole
from app.llm.exceptions import ModelExecutionError, FallbackUnavailableError
from app.config import settings

logger = logging.getLogger(__name__)

class ModelManager:
    def __init__(self, client: Optional[OllamaClient] = None, detector: Optional[ModelDetector] = None):
        self.client = client or OllamaClient()
        self.detector = detector or ModelDetector(self.client)
        self._active_model: Optional[str] = None
        self._previous_model: Optional[str] = None
        self._cache = None

    async def list_models(self, refresh: bool = False) -> List[str]:
        if refresh or self._cache is None:
            self._cache = await self.detector.get_installed_models()
        return self._cache

    def get_active_model(self) -> Optional[str]:
        return self._active_model

    def get_available_roles(self) -> List[str]:
        return list(MODELS.keys())

    async def get_model_status(self) -> Dict[str, str]:
        """Expose basic status of roles."""
        installed = await self.detector.get_installed_models()
        installed_normalized = [m.lower() for m in installed]
        
        status = {}
        for role, config in MODELS.items():
            model = config["model"]
            is_available = self.detector._check_match(model, installed_normalized)
            status[role] = "AVAILABLE" if is_available else "MISSING"
        return status

    async def resolve_model(self, role_or_model: str) -> str:
        """
        Resolves a role name or raw model name to an available installed model.
        Supports fallback path traversal and detects compatible alternatives.
        """
        # If it's not a registry role, treat it as a direct model name
        if role_or_model not in MODELS:
            if await self.detector.is_model_installed(role_or_model):
                return role_or_model
                
            # If the exact model isn't installed, check if a base match exists
            installed = await self.detector.get_installed_models()
            for m in installed:
                if m.lower().startswith(role_or_model.lower()):
                    logger.info(f"[XENO MODEL] Matched direct name '{role_or_model}' to installed model '{m}'")
                    return m
            
            # If not matching, fallback to registry 'general' role
            logger.warning(f"[XENO MODEL] Direct model '{role_or_model}' not found. Falling back to role selection.")
            role_or_model = ModelRole.GENERAL.value

        # Attempt to resolve the role traversing fallback paths
        attempted_roles = []
        current_role = role_or_model

        while current_role and current_role not in attempted_roles:
            attempted_roles.append(current_role)
            config = MODELS[current_role]
            primary_model = config["model"]

            # 1. Check if configured model is installed
            if await self.detector.is_model_installed(primary_model):
                return primary_model

            # 2. Try to search for a compatible matching model tag for this role
            compatible_model = await self.detector.find_compatible_model(current_role)
            if compatible_model:
                logger.info(f"[XENO MODEL] Primary model '{primary_model}' missing. Routing to compatible alternative '{compatible_model}' for role '{current_role}'")
                return compatible_model

            # 3. Traverse to configured fallback role
            fallback_role = config.get("fallback")
            if fallback_role:
                logger.warning(f"[XENO MODEL] Fallback activated: role '{current_role}' -> '{fallback_role}'")
            current_role = fallback_role

        # If fallback chain fails, check settings default fallback model
        default_model = getattr(settings, "OLLAMA_DEFAULT_MODEL", "qwen3.5:0.8b")
        if await self.detector.is_model_installed(default_model):
            logger.warning(f"[XENO MODEL] Fallback chain exhausted. Defaulting to settings configuration: '{default_model}'")
            return default_model

        # Check if there is absolutely any model installed
        installed_models = await self.detector.get_installed_models()
        if installed_models:
            fallback_any = installed_models[0]
            logger.warning(f"[XENO MODEL] Fallback exhausted. Using first available local model: '{fallback_any}'")
            return fallback_any

        # No models available anywhere
        raise FallbackUnavailableError(
            "XENO could not find an available local AI model. Start Ollama and install at least one configured model."
        )

    async def generate(
        self, 
        role_or_model: str, 
        messages: List[Dict[str, str]], 
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """Resolve model role and run complete generation synchronously (blocking wrapper)."""
        resolved_model = await self.resolve_model(role_or_model)
        self._update_active_model(resolved_model)
        
        # Merge options
        merged_options = self._get_options(role_or_model, options)
        keep_alive = self._get_keep_alive(role_or_model)
        
        try:
            return await self.client.generate(resolved_model, messages, merged_options, keep_alive)
        except Exception as e:
            logger.error(f"Generation failed on model '{resolved_model}': {e}")
            raise ModelExecutionError(f"Model execution error: {e}")

    async def stream(
        self, 
        role_or_model: str, 
        messages: List[Dict[str, str]], 
        options: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        """Resolve model role and stream response tokens."""
        resolved_model = await self.resolve_model(role_or_model)
        self._update_active_model(resolved_model)
        
        # Merge options
        merged_options = self._get_options(role_or_model, options)
        keep_alive = self._get_keep_alive(role_or_model)

        logger.info(f"[XENO MODEL] Selected model: {resolved_model} (Provider: ollama)")
        logger.info("[XENO MODEL] Streaming started")

        try:
            async for chunk in self.client.stream_chat(resolved_model, messages, merged_options, keep_alive):
                token = chunk.get("message", {}).get("content", "")
                if token:
                    yield token
            logger.info("[XENO MODEL] Generation completed")
        except Exception as e:
            logger.error(f"Stream generation failed on model '{resolved_model}': {e}")
            raise ModelExecutionError(f"Streaming model execution error: {e}")

    def _update_active_model(self, model_name: str):
        if self._active_model != model_name:
            self._previous_model = self._active_model
            self._active_model = model_name

    def _get_options(self, role_or_model: str, user_options: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        options = {}
        config = get_role_config(role_or_model)
        if config and "options" in config:
            options.update(config["options"])
        if user_options:
            options.update(user_options)
        return options

    def _get_keep_alive(self, role_or_model: str) -> str:
        config = get_role_config(role_or_model)
        if config and "keep_alive" in config:
            return config["keep_alive"]
        return "5m"  # Default fallback keep-alive duration