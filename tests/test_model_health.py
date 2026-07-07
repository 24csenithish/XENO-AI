# tests/test_model_health.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.llm.model_health import ModelHealth


@pytest.mark.asyncio
async def test_ollama_offline_status():
    client = MagicMock()
    client.health_check = AsyncMock(return_value=False)

    detector = MagicMock()
    health = ModelHealth(client=client, detector=detector)

    status = await health.get_health_status()
    assert status["ollama"] == "OFFLINE"
    assert status["models"]["general"] == "OLLAMA_OFFLINE"


@pytest.mark.asyncio
async def test_install_commands_generated():
    client = MagicMock()
    client.health_check = AsyncMock(return_value=True)

    detector = MagicMock()
    detector.get_installed_models = AsyncMock(return_value=["llama3.2:3b"])
    detector._check_match = MagicMock(return_value=False)
    detector.find_compatible_model = AsyncMock(return_value=None)
    detector.get_missing_models = AsyncMock(return_value={"coding": "qwen2.5-coder:7b"})
    detector.normalize_model_name = lambda m: m.lower()

    health = ModelHealth(client=client, detector=detector)
    status = await health.get_health_status()

    assert "ollama pull qwen2.5-coder:7b" in status["install_commands"]
