# app/api/routes/health.py
from fastapi import APIRouter
from app.llm.model_manager import ModelManager
from app.config import settings

router = APIRouter()

@router.get("/")
async def health_check():
    mm = ModelManager()
    models = await mm.list_models()
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "ollama": "connected" if models else "no models",
        "default_model": settings.OLLAMA_DEFAULT_MODEL,
        "models": models
    }