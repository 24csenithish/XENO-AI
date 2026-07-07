# app/llm/model_router.py
import re
import time
import logging
from typing import List, Dict, Any, Optional
from app.models.schemas import ModelRole, RoutingResult
from app.llm.ollama_client import OllamaClient
from app.core.exceptions import ModelNotFoundError

logger = logging.getLogger(__name__)

class ModelRouter:
    def __init__(self, client: Optional[OllamaClient] = None):
        self.client = client or OllamaClient()

    async def validate(self, model_name: str) -> str:
        """Check if model exists in Ollama; raise if not."""
        available = await self.client.list_models()
        if model_name not in available:
            # Try to match case-insensitively or without tags
            normalized = model_name.lower()
            matched = None
            for m in available:
                if m.lower() == normalized or (":" not in normalized and m.lower().split(":")[0] == normalized):
                    matched = m
                    break
            if matched:
                return matched
            raise ModelNotFoundError(f"Model '{model_name}' not found in Ollama. Available: {available}")
        return model_name

    def route(
        self, 
        prompt: str, 
        history: Optional[List[Dict[str, str]]] = None,
        has_image: bool = False
    ) -> RoutingResult:
        """
        Decides which AI model role should process the user prompt.
        Uses a hybrid routing strategy: Deterministic -> Weighted Scoring -> Contextual -> Fallback.
        """
        prompt_trimmed = prompt.strip()
        prompt_lower = prompt_trimmed.lower()
        word_count = len(prompt_trimmed.split())

        # --- Layer 1: Deterministic Layer ---
        # 1. Vision routing if image is present
        if has_image:
            return RoutingResult(
                role=ModelRole.VISION,
                confidence=1.0,
                reason="Deterministic: Image/screenshot attachment detected."
            )

        # 2. Coding Error deterministic match (stack trace, traceback)
        coding_error_patterns = [
            r"traceback\s+\(most\s+recent\s+call\s+last\):",
            r"syntaxerror:",
            r"importerror:",
            r"modulenotfounderror:",
            r"typeerror:",
            r"npm\s+err!",
            r"pnpm\s+error",
            r"failed\s+to\s+compile",
            r"undefined\s+is\s+not\s+an\s+object"
        ]
        for pattern in coding_error_patterns:
            if re.search(pattern, prompt_lower):
                return RoutingResult(
                    role=ModelRole.CODING,
                    confidence=0.98,
                    reason=f"Deterministic: Code traceback/error signature detected: '{pattern}'"
                )

        # 3. Explicit Code block detection
        if "```" in prompt_trimmed:
            return RoutingResult(
                role=ModelRole.CODING,
                confidence=0.97,
                reason="Deterministic: Markdown code blocks found in prompt."
            )

        # --- Layer 2: Weighted Intent Scoring Layer ---
        # Scoring tables
        scores = {
            ModelRole.FAST: 0.0,
            ModelRole.CODING: 0.0,
            ModelRole.REASONING: 0.0,
            ModelRole.GENERAL: 0.0
        }

        # Code keywords (exact matching where applicable)
        coding_keywords = [
            "python", "javascript", "typescript", "react", "vite", "fastapi", "flask",
            "node.js", "npm", "pnpm", "pip", "pyside6", "flutter", "dart", "sql", "git",
            "github", "docker", "kubernetes", "linux commands", "powershell", "bash",
            "class", "def ", "function", "const ", "let ", "import ", "require(", "async", "await",
            "database", "json", "yaml", "toml", "xml", "api", "endpoint", "debugging", "array", "struct",
            "code", "coding", "program", "developer", "software", "script", "quicksort", "traceback"
        ]
        
        # Reasoning keywords
        reasoning_keywords = [
            "compare", "architecture", "inefficient", "scale", "performance", "trade-off",
            "bottleneck", "step-by-step", "deeply", "why", "root cause", "explain the difference",
            "monolith", "microservice", "distributed", "concurrency", "deadlock", "optimize",
            "logical", "puzzle", "prove", "derivation"
        ]

        # Fast keywords (greetings and short statements)
        fast_keywords = [
            "hello", "hi", "hey", "thanks", "thank you", "ok", "okay", "yes", "no", "bye", "greetings"
        ]

        # Heuristic checks
        # Fast model boosts
        if word_count <= 5:
            # Check if any greeting keyword matches exactly or as a token
            has_greeting = False
            for k in fast_keywords:
                # Matches word boundary
                if re.search(r'\b' + re.escape(k) + r'\b', prompt_lower):
                    has_greeting = True
                    break
            
            if has_greeting:
                scores[ModelRole.FAST] += 0.8
            elif word_count <= 3:
                scores[ModelRole.FAST] += 0.4  # general short boost only if <= 3 words

        # Keyword match scoring
        for kw in coding_keywords:
            if kw in prompt_lower:
                scores[ModelRole.CODING] += 0.35

        for kw in reasoning_keywords:
            if kw in prompt_lower:
                scores[ModelRole.REASONING] += 0.35

        # --- Layer 3: Context-Aware Adjustments ---
        if history:
            # Retrieve last interactions
            last_user_msgs = [m for m in history if m["role"] == "user"]
            last_assistant_msgs = [m for m in history if m["role"] == "assistant"]
            
            # If the user asks a very short question (like "why?", "explain more"),
            # it should carry over the context of the previous model rather than defaulting to FAST.
            if word_count <= 4 and last_user_msgs:
                prev_text = last_user_msgs[-1]["content"].lower()
                # Run temporary lightweight classification on previous text to infer previous active role
                prev_route = self.route(prev_text, history=None, has_image=False)
                if prev_route.role in [ModelRole.CODING, ModelRole.REASONING]:
                    scores[prev_route.role] += 0.9  # strongly persist context
                    logger.debug(f"Routing carryover: inheriting previous classification context: {prev_route.role}")

        # Choose category with highest score
        best_role = max(scores, key=scores.get)
        best_score = scores[best_role]

        # Threshold check
        if best_score > 0.3:
            # Normalize confidence between 0.6 and 0.99
            confidence = min(0.6 + (best_score * 0.4), 0.99)
            return RoutingResult(
                role=best_role,
                confidence=confidence,
                reason=f"Weighted Heuristics: Selected {best_role.value} with confidence {confidence:.2f}."
            )

        # --- Layer 4: Fallback to General ---
        return RoutingResult(
            role=ModelRole.GENERAL,
            confidence=0.5,
            reason="Fallback: Heuristics low confidence; routing default general model."
        )
