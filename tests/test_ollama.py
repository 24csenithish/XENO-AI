# tests/test_ollama.py
import pytest
from app.llm.ollama_client import OllamaClient

@pytest.mark.asyncio
async def test_list_models():
    client = OllamaClient()
    models = await client.list_models()
    assert isinstance(models, list)