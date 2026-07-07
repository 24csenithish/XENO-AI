# app/llm/startup.py
import logging
from typing import Dict, List
from app.llm.ollama_client import OllamaClient
from app.llm.model_detector import ModelDetector
from app.llm.model_registry import MODELS

logger = logging.getLogger(__name__)


async def run_startup_model_check(client: OllamaClient = None) -> Dict[str, str]:
    """
    Check Ollama connectivity and log model availability at startup.
    Returns per-role status dict.
    """
    client = client or OllamaClient()
    detector = ModelDetector(client)
    status: Dict[str, str] = {}

    is_online = await client.health_check()
    if not is_online:
        logger.warning("[XENO LLM] Ollama OFFLINE")
        for role in MODELS:
            status[role] = "MISSING"
        return status

    installed = await detector.get_installed_models()
    logger.info("[XENO LLM] Ollama ONLINE")
    logger.info("[XENO LLM] Detected %d local models", len(installed))

    for role, config in MODELS.items():
        model = config["model"]
        is_available = await detector.is_model_installed(model)
        if not is_available:
            compatible = await detector.find_compatible_model(role)
            if compatible:
                is_available = True
                model = compatible

        if is_available:
            status[role] = "AVAILABLE"
            logger.info("[XENO LLM] %s model AVAILABLE: %s", role.capitalize(), model)
        else:
            status[role] = "MISSING"
            logger.warning("[XENO LLM] %s model MISSING: %s", role.capitalize(), config["model"])

    missing = await detector.get_missing_models()
    if missing:
        logger.info("[XENO LLM] Install missing models with:")
        for role, model_name in missing.items():
            logger.info("[XENO LLM]   ollama pull %s  # %s role", model_name, role)

    return status


def get_install_commands(missing: Dict[str, str]) -> List[str]:
    """Generate ollama pull commands for missing registry models."""
    return [f"ollama pull {model}" for model in missing.values()]
