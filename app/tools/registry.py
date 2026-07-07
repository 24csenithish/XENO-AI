# app/tools/registry.py
from typing import Dict, Callable, Any
import logging

logger = logging.getLogger(__name__)

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}

    def register(self, name: str, func: Callable, description: str, parameters: Dict = None):
        self._tools[name] = {
            "func": func,
            "description": description,
            "parameters": parameters or {}
        }
        logger.info(f"Tool registered: {name}")

    def get_descriptions(self) -> Dict[str, str]:
        return {name: info["description"] for name, info in self._tools.items()}

    async def execute(self, name: str, **kwargs) -> Any:
        if name not in self._tools:
            raise ValueError(f"Tool '{name}' not found")
        try:
            result = await self._tools[name]["func"](**kwargs)
            return result
        except Exception as e:
            logger.exception(f"Tool execution failed: {name}")
            return {"error": str(e)}