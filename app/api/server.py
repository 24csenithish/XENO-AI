# app/api/server.py
from fastapi import FastAPI
from app.api.routes import chat, conversations, models, health
from app.database.database import engine, Base
from app.config import settings

def create_app() -> FastAPI:
    app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)
    # Create tables if not exist
    Base.metadata.create_all(bind=engine)

    app.include_router(health.router, prefix="/health", tags=["health"])
    app.include_router(models.router, prefix="/models", tags=["models"])
    app.include_router(chat.router, prefix="/chat", tags=["chat"])
    app.include_router(conversations.router, prefix="/conversations", tags=["conversations"])

    return app