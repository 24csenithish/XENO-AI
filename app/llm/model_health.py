# app/llm/model_health.py
import logging
from typing import Dict, Any, Optional, List
from app.llm.ollama_client import OllamaClient
from app.llm.model_detector import ModelDetector
from app.llm.model_registry import MODELS
from app.llm.startup import get_install_commands

logger = logging.getLogger(__name__)


class ModelHealth:
    def __init__(self, client: Optional[OllamaClient] = None, detector: Optional[ModelDetector] = None):
        self.client = client or OllamaClient()
        self.detector = detector or ModelDetector(self.client)

    async def get_health_status(self, active_model: Optional[str] = None) -> Dict[str, Any]:
        """Check connection health and build availability dictionary for registry model roles."""
        is_online = await self.client.health_check()

        status: Dict[str, Any] = {
            "ollama": "ONLINE" if is_online else "OFFLINE",
            "active_model": active_model or "None",
            "models": {},
            "install_commands": [],
        }

        if is_online:
            installed = await self.detector.get_installed_models()
            installed_normalized = [
                self.detector.normalize_model_name(m) for m in installed
            ]

            for role, config in MODELS.items():
                model = config["model"]
                is_available = self.detector._check_match(model, installed_normalized)
                if not is_available:
                    compatible = await self.detector.find_compatible_model(role)
                    is_available = compatible is not None
                status["models"][role] = "AVAILABLE" if is_available else "MISSING"

            missing = await self.detector.get_missing_models()
            status["install_commands"] = get_install_commands(missing)
        else:
            for role in MODELS:
                status["models"][role] = "OLLAMA_OFFLINE"

        return status

    async def get_role_status_summary(self) -> List[Dict[str, str]]:
        """Return structured per-role health for API consumers."""
        health = await self.get_health_status()
        summary = []
        for role, config in MODELS.items():
            summary.append({
                "role": role,
                "model": config["model"],
                "provider": config.get("provider", "ollama"),
                "status": health["models"].get(role, "UNKNOWN"),
            })
        return summary
