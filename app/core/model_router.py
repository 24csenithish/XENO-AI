# app/core/model_router.py
from app.llm.model_router import ModelRouter as NewModelRouter

class ModelRouter(NewModelRouter):
    """Deprecated: Backward-compatible wrapper for app.llm.model_router.ModelRouter."""
    pass