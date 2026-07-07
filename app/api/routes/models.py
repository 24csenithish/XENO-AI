# app/api/routes/models.py
from fastapi import APIRouter
from app.llm.model_manager import ModelManager
from app.llm.model_health import ModelHealth
from app.llm.model_registry import MODELS

router = APIRouter()
mm = ModelManager()
health = ModelHealth(mm.client, mm.detector)

@router.get("/")
async def list_models():
    """Returns configured local model roles."""
    return {"models": list(MODELS.keys()), "registry": MODELS}

@router.get("/status")
async def get_status():
    """Returns model health."""
    active_model = mm.get_active_model()
    return await health.get_health_status(active_model)

@router.get("/installed")
async def get_installed():
    """Returns locally detected Ollama models."""
    return {"installed": await mm.list_models(refresh=True)}