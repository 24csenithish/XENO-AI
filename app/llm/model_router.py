# app/llm/model_router.py
import re
import time
import logging
from typing import List, Dict, Optional
from app.models.schemas import ModelRole, RoutingResult
from app.llm.ollama_client import OllamaClient
from app.core.exceptions import ModelNotFoundError
from app.config import settings

logger = logging.getLogger(__name__)

FILE_EXTENSION_PATTERN = re.compile(
    r"\.(py|js|ts|tsx|jsx|cpp|c|java|dart|sql|sh|ps1|yaml|yml|json|toml)\b",
    re.IGNORECASE,
)

CONTEXT_EXPIRY_SECONDS = 600  # 10 minutes


class ModelRouter:
    def __init__(self, client: Optional[OllamaClient] = None):
        self.client = client or OllamaClient()
        self._previous_role: Optional[ModelRole] = None
        self._previous_confidence: float = 0.0
        self._conversation_topic: Optional[str] = None
        self._last_route_timestamp: float = 0.0

    async def validate(self, model_name: str) -> str:
        """Check if model exists in Ollama; raise if not."""
        available = await self.client.list_models()
        if model_name not in available:
            normalized = model_name.lower()
            matched = None
            for m in available:
                if m.lower() == normalized or (
                    ":" not in normalized and m.lower().split(":")[0] == normalized
                ):
                    matched = m
                    break
            if matched:
                return matched
            raise ModelNotFoundError(
                f"Model '{model_name}' not found in Ollama. Available: {available}"
            )
        return model_name

    def route(
        self,
        prompt: str,
        history: Optional[List[Dict[str, str]]] = None,
        has_image: bool = False,
        previous_role: Optional[str] = None,
    ) -> RoutingResult:
        """
        Decides which AI model role should process the user prompt.
        Uses a hybrid routing strategy: Deterministic -> Weighted Scoring -> Contextual -> Fallback.
        """
        prompt_trimmed = prompt.strip()
        prompt_lower = prompt_trimmed.lower()
        word_count = len(prompt_trimmed.split())

        # --- Layer 1: Deterministic Layer ---
        if has_image:
            result = RoutingResult(
                role=ModelRole.VISION,
                confidence=1.0,
                reason="Deterministic: Image/screenshot attachment detected.",
            )
            self._update_context(result, prompt_trimmed)
            return result

        coding_error_patterns = [
            r"traceback\s+\(most\s+recent\s+call\s+last\):",
            r"syntaxerror:",
            r"importerror:",
            r"modulenotfounderror:",
            r"typeerror:",
            r"npm\s+err!",
            r"pnpm\s+error",
            r"failed\s+to\s+compile",
            r"undefined\s+is\s+not\s+an\s+object",
        ]
        for pattern in coding_error_patterns:
            if re.search(pattern, prompt_lower):
                result = RoutingResult(
                    role=ModelRole.CODING,
                    confidence=0.98,
                    reason=f"Deterministic: Code traceback/error signature detected.",
                )
                self._update_context(result, prompt_trimmed)
                return result

        if "```" in prompt_trimmed:
            result = RoutingResult(
                role=ModelRole.CODING,
                confidence=0.97,
                reason="Deterministic: Markdown code blocks found in prompt.",
            )
            self._update_context(result, prompt_trimmed)
            return result

        if FILE_EXTENSION_PATTERN.search(prompt_trimmed):
            result = RoutingResult(
                role=ModelRole.CODING,
                confidence=0.95,
                reason="Deterministic: Programming file extension detected.",
            )
            self._update_context(result, prompt_trimmed)
            return result

        # --- Layer 2: Weighted Intent Scoring Layer ---
        scores = {
            ModelRole.FAST: 0.0,
            ModelRole.CODING: 0.0,
            ModelRole.REASONING: 0.0,
            ModelRole.GENERAL: 0.1,
        }

        coding_keywords = [
            "python", "javascript", "typescript", "react", "vite", "fastapi", "flask",
            "node.js", "npm", "pnpm", "pip", "pyside6", "flutter", "dart", "sql", "git",
            "github", "docker", "kubernetes", "linux commands", "powershell", "bash",
            "class", "def ", "function", "const ", "let ", "import ", "require(", "async", "await",
            "database", "json", "yaml", "toml", "xml", "api", "endpoint", "debugging", "array",
            "code", "coding", "program", "developer", "software", "script", "quicksort", "traceback",
            "write python", "fix error", "debug", "compile", "syntax",
        ]

        reasoning_keywords = [
            "compare", "architecture", "inefficient", "scale", "performance", "trade-off",
            "bottleneck", "step-by-step", "step by step", "deeply", "root cause",
            "explain the difference", "monolith", "microservice", "distributed",
            "concurrency", "deadlock", "optimize", "logical", "puzzle", "prove", "derivation",
            "evaluate", "analyze deeply", "design a complex",
        ]

        fast_keywords = [
            "hello", "hi", "hey", "thanks", "thank you", "ok", "okay", "yes", "no", "bye", "greetings",
        ]

        has_technical_error = any(
            kw in prompt_lower
            for kw in ["npm err", "traceback", "error", "exception", "failed", "modulenotfound"]
        )

        if word_count <= 5 and not has_technical_error:
            has_greeting = any(
                re.search(r"\b" + re.escape(k) + r"\b", prompt_lower) for k in fast_keywords
            )
            if has_greeting:
                scores[ModelRole.FAST] += 0.8
            elif word_count <= 3:
                scores[ModelRole.FAST] += 0.4

        for kw in coding_keywords:
            if kw in prompt_lower:
                scores[ModelRole.CODING] += 0.35

        for kw in reasoning_keywords:
            if kw in prompt_lower:
                scores[ModelRole.REASONING] += 0.35

        if re.search(r"\bwhy\b", prompt_lower) and word_count > 4:
            scores[ModelRole.REASONING] += 0.3

        # --- Layer 3: Context-Aware Adjustments ---
        if settings.XENO_ROUTER_CONTEXT:
            self._expire_context_if_needed()

            if word_count <= 4 and (history or self._previous_role):
                carry_role = None
                if previous_role:
                    try:
                        carry_role = ModelRole(previous_role)
                    except ValueError:
                        pass
                elif self._previous_role and self._previous_role in (
                    ModelRole.CODING, ModelRole.REASONING
                ):
                    carry_role = self._previous_role

                if not carry_role and history:
                    last_user_msgs = [m for m in history if m["role"] == "user"]
                    if last_user_msgs:
                        prev_text = last_user_msgs[-1]["content"].lower()
                        prev_route = self.route(prev_text, history=None, has_image=False)
                        if prev_route.role in (ModelRole.CODING, ModelRole.REASONING):
                            carry_role = prev_route.role

                if carry_role:
                    scores[carry_role] += 0.9
                    logger.debug(
                        "[XENO ROUTER] Context carryover: inheriting %s", carry_role.value
                    )

        best_role = max(scores, key=scores.get)
        best_score = scores[best_role]

        if best_score > 0.3:
            confidence = min(0.6 + (best_score * 0.4), 0.99)
            result = RoutingResult(
                role=best_role,
                confidence=confidence,
                reason=f"Weighted heuristics: {best_role.value} (score={best_score:.2f}).",
            )
            self._update_context(result, prompt_trimmed)
            return result

        # --- Layer 4: Fallback to General ---
        result = RoutingResult(
            role=ModelRole.GENERAL,
            confidence=0.5,
            reason="Fallback: Low confidence; routing to general model.",
        )
        self._update_context(result, prompt_trimmed)
        return result

    def _update_context(self, result: RoutingResult, prompt: str) -> None:
        self._previous_role = result.role
        self._previous_confidence = result.confidence
        self._conversation_topic = prompt[:80] if prompt else None
        self._last_route_timestamp = time.time()

    def _expire_context_if_needed(self) -> None:
        if self._last_route_timestamp and (
            time.time() - self._last_route_timestamp > CONTEXT_EXPIRY_SECONDS
        ):
            self._previous_role = None
            self._previous_confidence = 0.0
            self._conversation_topic = None

    def get_routing_context(self) -> Dict[str, object]:
        return {
            "previous_role": self._previous_role.value if self._previous_role else None,
            "previous_confidence": self._previous_confidence,
            "conversation_topic": self._conversation_topic,
            "last_route_timestamp": self._last_route_timestamp,
        }
