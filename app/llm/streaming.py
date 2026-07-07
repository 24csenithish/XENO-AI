# app/llm/streaming.py
from typing import Dict, Any

class StreamProcessor:
    @staticmethod
    def extract_content(chunk: Dict[str, Any]) -> str:
        """Extract message content from Ollama chunk."""
        return chunk.get("message", {}).get("content", "")