# tests/test_model_manager.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.llm.model_manager import ModelManager
from app.llm.exceptions import FallbackUnavailableError
from app.llm.model_detector import ModelDetector


class FakeDetector:
    def __init__(self, installed=None):
        self.installed = installed or []

    async def get_installed_models(self):
        return self.installed

    async def is_model_installed(self, model_name):
        normalized = model_name.lower()
        for m in self.installed:
            if m.lower() == normalized:
                return True
            if ":" not in normalized and m.lower().split(":")[0] == normalized:
                return True
        return False

    async def find_compatible_model(self, role):
        return None

    def _check_match(self, model_name, installed_list):
        return ModelDetector._check_match(None, model_name, installed_list)

    @staticmethod
    def normalize_model_name(name):
        return ModelDetector.normalize_model_name(name)


@pytest.mark.asyncio
async def test_resolve_coding_fallback_to_general():
    detector = FakeDetector(installed=["qwen3:8b"])
    mm = ModelManager(detector=detector)

    resolved = await mm.resolve_model("coding")
    assert resolved == "qwen3:8b"
    assert mm.get_active_role() == "general"


@pytest.mark.asyncio
async def test_resolve_reasoning_fallback_chain():
    detector = FakeDetector(installed=["llama3.2:3b"])
    mm = ModelManager(detector=detector)

    resolved = await mm.resolve_model("reasoning")
    assert resolved == "llama3.2:3b"


@pytest.mark.asyncio
async def test_no_models_raises_fallback_unavailable():
    detector = FakeDetector(installed=[])
    mm = ModelManager(detector=detector)

    with pytest.raises(FallbackUnavailableError):
        await mm.resolve_model("coding")


@pytest.mark.asyncio
async def test_fallback_loop_prevention():
    """Ensure attempted roles are tracked and loop terminates."""
    detector = FakeDetector(installed=[])
    mm = ModelManager(detector=detector)

    with patch.object(detector, "find_compatible_model", new_callable=AsyncMock, return_value=None):
        with pytest.raises(FallbackUnavailableError):
            await mm.resolve_model("fast")


def test_normalize_model_name():
    assert ModelDetector.normalize_model_name("QWEN3:8B") == "qwen3:8b"
    assert ModelDetector.normalize_model_name("  qwen3  ") == "qwen3"
