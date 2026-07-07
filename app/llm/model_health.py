# app/llm/model_health.py
import logging
from typing import Dict, Any, Optional
from app.llm.ollama_client import OllamaClient
from app.llm.model_detector import ModelDetector
from app.llm.model_registry import MODELS

logger = logging.getLogger(__name__)

class ModelHealth:
    def __init__(self, client: Optional[OllamaClient] = None, detector: Optional[ModelDetector] = None):
        self.client = client or OllamaClient()
        self.detector = detector or ModelDetector(self.client)

    async def get_health_status(self, active_model: Optional[str] = None) -> Dict[str, Any]:
        """Check connection health and build availability dictionary for registry model roles."""
        is_online = await self.client.health_check()
        
        status = {
            "ollama": "ONLINE" if is_online else "OFFLINE",
            "active_model": active_model or "None",
            "models": {}
        }
        
        if is_online:
            installed = await self.detector.get_installed_models()
            installed_normalized = [m.lower() for m in installed]
            
            for role, config in MODELS.items():
                model = config["model"]
                is_available = self.detector._check_match(model, installed_normalized)
                status["models"][role] = "AVAILABLE" if is_available else "MISSING"
        else:
            for role in MODELS.keys():
                status["models"][role] = "MISSING"
                
        return status
