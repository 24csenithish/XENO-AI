# app/llm/ollama_client.py
import httpx
import json
import logging
from typing import AsyncGenerator, List, Dict, Any, Optional
from app.config import settings
from app.llm.base import BaseLLM
from app.llm.exceptions import OllamaConnectionError

logger = logging.getLogger(__name__)

class OllamaClient(BaseLLM):
    _client: Optional[httpx.AsyncClient] = None

    def __init__(self, host: str = None):
        # Support both OLLAMA_BASE_URL and OLLAMA_HOST settings
        self.host = host or getattr(settings, "OLLAMA_BASE_URL", None) or getattr(settings, "OLLAMA_HOST", "http://localhost:11434")
        self.timeout = settings.OLLAMA_TIMEOUT

    async def get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(base_url=self.host, timeout=httpx.Timeout(self.timeout))
        return self._client

    async def close(self):
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def generate(
        self, 
        model: str, 
        messages: List[Dict[str, str]], 
        options: Optional[Dict[str, Any]] = None,
        keep_alive: Optional[str] = None
    ) -> str:
        url = "/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": options or {}
        }
        if keep_alive:
            payload["keep_alive"] = keep_alive
            
        client = await self.get_client()
        try:
            resp = await client.post(url, json=payload)
            if resp.status_code != 200:
                raise OllamaConnectionError(f"Ollama error {resp.status_code}: {resp.text}")
            data = resp.json()
            return data.get("message", {}).get("content", "")
        except httpx.HTTPError as e:
            raise OllamaConnectionError(f"Failed to connect to Ollama: {e}")

    async def stream_chat(
        self, 
        model: str, 
        messages: List[Dict[str, str]], 
        options: Optional[Dict[str, Any]] = None,
        keep_alive: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        url = "/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": options or {}
        }
        if keep_alive:
            payload["keep_alive"] = keep_alive

        client = await self.get_client()
        try:
            async with client.stream("POST", url, json=payload) as response:
                if response.status_code != 200:
                    text = await response.aread()
                    raise OllamaConnectionError(f"Ollama error {response.status_code}: {text.decode('utf-8')}")
                async for line in response.aiter_lines():
                    if line:
                        try:
                            chunk = json.loads(line)
                            yield chunk
                        except json.JSONDecodeError:
                            continue
        except httpx.HTTPError as e:
            raise OllamaConnectionError(f"Failed to connect to Ollama: {e}")

    async def health_check(self) -> bool:
        client = await self.get_client()
        try:
            resp = await client.get("/")
            return resp.status_code == 200
        except:
            return False

    async def list_models(self) -> List[str]:
        client = await self.get_client()
        try:
            resp = await client.get("/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                return [m["name"] for m in data.get("models", [])]
            return []
        except Exception as e:
            logger.warning(f"Failed to fetch model list from Ollama: {e}")
            return []

    async def model_exists(self, model_name: str) -> bool:
        models = await self.list_models()
        normalized = model_name.lower()
        for m in models:
            m_lower = m.lower()
            if m_lower == normalized:
                return True
            # Also check base model name without tag
            if ":" not in normalized and m_lower.split(":")[0] == normalized:
                return True
        return False