# app/config.py
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    # XENO General
    APP_NAME: str = "XENO AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Ollama
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_DEFAULT_MODEL: str = "qwen3.5:0.8b"   # lightweight, suitable for 4GB
    OLLAMA_TIMEOUT: int = 60
    OLLAMA_STREAM: bool = True

    # Database
    DATABASE_URL: str = "sqlite:///storage/xeno.db"

    # Chat / Memory
    SHORT_TERM_MESSAGE_LIMIT: int = 12           # number of recent messages to include
    LONG_TERM_MEMORY_ENABLED: bool = False
    MAX_CONTEXT_TOKENS: int = 4096               # conservative for 4GB

    # RAG
    RAG_ENABLED: bool = False
    RAG_EMBEDDING_MODEL: str = "nomic-embed-text" # Ollama embedding model
    RAG_TOP_K: int = 4

    # Tools
    ENABLE_PYTHON_TOOL: bool = False             # disabled by default for security
    ENABLE_SYSTEM_INFO_TOOL: bool = True

    # Multi-LLM Offline Settings
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    XENO_DEFAULT_MODEL_ROLE: str = "general"
    XENO_ENABLE_MODEL_ROUTING: bool = True
    XENO_ROUTER_CONTEXT: bool = True
    XENO_MAX_HISTORY_MESSAGES: int = 20
    XENO_MODEL_DEBUG: bool = False
    XENO_STREAMING: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()