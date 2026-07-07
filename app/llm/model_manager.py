# app/llm/model_manager.py
import logging
from typing import AsyncGenerator, Dict, Any, List, Optional
from app.llm.ollama_client import OllamaClient
from app.llm.model_detector import ModelDetector
from app.llm.model_registry import MODELS, get_role_config
from app.llm.providers import get_provider_client
from app.llm.base import BaseLLM
from app.models.schemas import ModelRole
from app.llm.exceptions import ModelExecutionError, FallbackUnavailableError, OllamaConnectionError
from app.config import settings

logger = logging.getLogger(__name__)


class ModelManager:
    def __init__(self, client: Optional[OllamaClient] = None, detector: Optional[ModelDetector] = None):
        self.client = client or OllamaClient()
        self.detector = detector or ModelDetector(self.client)
        self._active_model: Optional[str] = None
        self._previous_model: Optional[str] = None
        self._active_role: Optional[str] = None
        self._cache: Optional[List[str]] = None
        self._provider_clients: Dict[str, BaseLLM] = {"ollama": self.client}

    def _get_client_for_role(self, role_or_model: str) -> BaseLLM:
        config = get_role_config(role_or_model)
        provider = config.get("provider", "ollama") if config else "ollama"
        if provider not in self._provider_clients:
            self._provider_clients[provider] = get_provider_client(provider)
        return self._provider_clients[provider]

    async def list_models(self, refresh: bool = False) -> List[str]:
        if refresh or self._cache is None:
            self._cache = await self.detector.get_installed_models()
        return self._cache

    def get_active_model(self) -> Optional[str]:
        return self._active_model

    def get_active_role(self) -> Optional[str]:
        return self._active_role

    def get_available_roles(self) -> List[str]:
        return list(MODELS.keys())

    async def get_model_status(self) -> Dict[str, str]:
        """Expose basic status of roles."""
        installed = await self.detector.get_installed_models()
        installed_normalized = [self.detector.normalize_model_name(m) for m in installed]

        status = {}
        for role, config in MODELS.items():
            model = config["model"]
            is_available = self.detector._check_match(model, installed_normalized)
            if not is_available:
                compatible = await self.detector.find_compatible_model(role)
                is_available = compatible is not None
            status[role] = "AVAILABLE" if is_available else "MISSING"
        return status

    async def resolve_model(self, role_or_model: str) -> str:
        """
        Resolves a role name or raw model name to an available installed model.
        Supports fallback path traversal and detects compatible alternatives.
        """
        if role_or_model not in MODELS:
            if await self.detector.is_model_installed(role_or_model):
                self._active_role = None
                return role_or_model

            installed = await self.detector.get_installed_models()
            for m in installed:
                if m.lower().startswith(role_or_model.lower()):
                    logger.info(
                        "[XENO MODEL] Matched direct name '%s' to installed model '%s'",
                        role_or_model, m,
                    )
                    self._active_role = None
                    return m

            logger.warning(
                "[XENO MODEL] Direct model '%s' not found. Falling back to role selection.",
                role_or_model,
            )
            role_or_model = ModelRole.GENERAL.value

        attempted_roles: List[str] = []
        current_role = role_or_model

        while current_role and current_role not in attempted_roles:
            attempted_roles.append(current_role)
            config = MODELS[current_role]
            primary_model = config["model"]

            if await self.detector.is_model_installed(primary_model):
                self._active_role = current_role
                return primary_model

            compatible_model = await self.detector.find_compatible_model(current_role)
            if compatible_model:
                logger.info(
                    "[XENO MODEL] Primary model '%s' missing. Routing to compatible '%s' for role '%s'",
                    primary_model, compatible_model, current_role,
                )
                self._active_role = current_role
                return compatible_model

            fallback_role = config.get("fallback")
            if fallback_role:
                logger.warning(
                    "[XENO MODEL] Fallback activated: %s -> %s",
                    current_role, fallback_role,
                )
            current_role = fallback_role

        default_model = getattr(settings, "OLLAMA_DEFAULT_MODEL", "qwen3.5:0.8b")
        if await self.detector.is_model_installed(default_model):
            logger.warning(
                "[XENO MODEL] Fallback chain exhausted. Defaulting to: '%s'",
                default_model,
            )
            self._active_role = ModelRole.GENERAL.value
            return default_model

        installed_models = await self.detector.get_installed_models()
        if installed_models:
            fallback_any = installed_models[0]
            logger.warning(
                "[XENO MODEL] Fallback exhausted. Using first available: '%s'",
                fallback_any,
            )
            self._active_role = ModelRole.GENERAL.value
            return fallback_any

        raise FallbackUnavailableError(
            "XENO could not find an available local AI model. "
            "Start Ollama and install at least one configured model."
        )

    async def generate(
        self,
        role_or_model: str,
        messages: List[Dict[str, str]],
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Resolve model role and run complete generation."""
        resolved_model = await self.resolve_model(role_or_model)
        self._update_active_model(resolved_model)

        merged_options = self._get_options(role_or_model, options)
        keep_alive = self._get_keep_alive(role_or_model)
        client = self._get_client_for_role(role_or_model)

        logger.info("[XENO MODEL] Requested role: %s", role_or_model)
        logger.info("[XENO MODEL] Selected model: %s", resolved_model)
        logger.info("[XENO MODEL] Provider: ollama")

        try:
            return await client.generate(resolved_model, messages, merged_options, keep_alive)
        except OllamaConnectionError:
            raise
        except Exception as e:
            logger.error("Generation failed on model '%s': %s", resolved_model, e)
            raise ModelExecutionError(f"Model execution error: {e}")

    async def stream(
        self,
        role_or_model: str,
        messages: List[Dict[str, str]],
        options: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[str, None]:
        """Resolve model role and stream response tokens."""
        resolved_model = await self.resolve_model(role_or_model)
        self._update_active_model(resolved_model)

        merged_options = self._get_options(role_or_model, options)
        keep_alive = self._get_keep_alive(role_or_model)
        client = self._get_client_for_role(role_or_model)

        logger.info("[XENO MODEL] Requested role: %s", role_or_model)
        logger.info("[XENO MODEL] Selected model: %s", resolved_model)
        logger.info("[XENO MODEL] Provider: ollama")
        logger.info("[XENO MODEL] Streaming started")

        try:
            async for chunk in client.stream_chat(
                resolved_model, messages, merged_options, keep_alive
            ):
                token = chunk.get("message", {}).get("content", "")
                if token:
                    yield token
            logger.info("[XENO MODEL] Generation completed")
        except OllamaConnectionError:
            raise
        except Exception as e:
            logger.error("Stream generation failed on model '%s': %s", resolved_model, e)
            raise ModelExecutionError(f"Streaming model execution error: {e}")

    def _update_active_model(self, model_name: str) -> None:
        if self._active_model != model_name:
            self._previous_model = self._active_model
            self._active_model = model_name

    def _get_options(self, role_or_model: str, user_options: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        options: Dict[str, Any] = {}
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
        return "5m"

    async def close(self) -> None:
        """Close all provider client connections."""
        for client in self._provider_clients.values():
            if hasattr(client, "close"):
                await client.close()
