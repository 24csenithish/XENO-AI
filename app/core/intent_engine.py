# app/core/intent_engine.py
from pydantic import BaseModel
from typing import Optional

class IntentResult(BaseModel):
    requires_tool: bool = False
    tool_name: Optional[str] = None

class IntentEngine:
    def __init__(self):
        pass

    async def detect(self, prompt: str) -> IntentResult:
        """Analyze prompt to determine if external tools are requested."""
        prompt_lower = prompt.lower()
        
        # Simple heuristics for tool invocation
        if "execute python" in prompt_lower or "run python" in prompt_lower:
            return IntentResult(requires_tool=True, tool_name="python_exec")
            
        if "system info" in prompt_lower or "cpu usage" in prompt_lower:
            return IntentResult(requires_tool=True, tool_name="system_info")
            
        return IntentResult(requires_tool=False)
