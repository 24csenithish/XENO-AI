# app/core/prompts.py
from typing import List, Dict, Any

XENO_IDENTITY = """You are XENO, a developer-focused artificial intelligence assistant.
Your purpose is to provide clear, accurate, and practical technical guidance.
You specialise in software development, system architecture, AI, automation, and DevOps.
You respond in a professional, futuristic, and concise manner.
Avoid repetitive self-introductions or mentioning your underlying model.
If you don't know something, say so clearly.
You support English and Tamil-English mixed conversations where possible.
Your tone is helpful, technical, and direct.
"""

def build_system_prompt(
    long_term_memory: List[Dict[str, Any]] = None,
    rag_context: List[str] = None,
    tool_descriptions: Dict[str, str] = None
) -> str:
    """Assemble the full system prompt with all contextual layers."""
    parts = [XENO_IDENTITY]

    if long_term_memory:
        mem_text = "\n".join([m["content"] for m in long_term_memory])
        parts.append(f"\n[LONG-TERM MEMORY]\n{mem_text}")

    if rag_context:
        rag_text = "\n".join(rag_context)
        parts.append(f"\n[KNOWLEDGE BASE]\n{rag_text}")

    if tool_descriptions:
        tool_text = "\n".join([f"- {name}: {desc}" for name, desc in tool_descriptions.items()])
        parts.append(f"\n[AVAILABLE TOOLS]\n{tool_text}")

    # Additional instructions about tool usage, if any
    parts.append("\nWhen using tools, follow the provided tool descriptions carefully.")
    return "\n".join(parts)