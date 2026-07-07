# app/api/server.py
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.routes import chat, conversations, models, health
from app.database.database import engine, Base
from app.config import settings
from app.llm.startup import run_startup_model_check
from app.llm.ollama_client import OllamaClient

logger = logging.getLogger(__name__)
_shared_client = OllamaClient()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.basicConfig(level=logging.INFO if not settings.DEBUG else logging.DEBUG)
    await run_startup_model_check(_shared_client)
    yield
    await _shared_client.close()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        lifespan=lifespan,
    )
    Base.metadata.create_all(bind=engine)

    app.include_router(health.router, prefix="/health", tags=["health"])
    app.include_router(models.router, prefix="/models", tags=["models"])
    app.include_router(chat.router, prefix="/chat", tags=["chat"])
    app.include_router(conversations.router, prefix="/conversations", tags=["conversations"])

    return app
