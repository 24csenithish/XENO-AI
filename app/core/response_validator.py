# app/core/response_validator.py
import re
import logging

logger = logging.getLogger(__name__)


class ResponseValidator:
    def __init__(self):
        self.identity_leaks = [
            (re.compile(r"\bI am Qwen\b", re.IGNORECASE), "I am XENO AI"),
            (re.compile(r"\bI am a language model developed by Alibaba\b", re.IGNORECASE), "I am a local model orchestrating XENO AI"),
            (re.compile(r"\bI'm Qwen\b", re.IGNORECASE), "I'm XENO AI"),
            (re.compile(r"\bdeveloped by Alibaba\b", re.IGNORECASE), "developed by the XENO AI team"),
            (re.compile(r"\bI am DeepSeek\b", re.IGNORECASE), "I am XENO AI"),
            (re.compile(r"\bI am a language model developed by DeepSeek\b", re.IGNORECASE), "I am a local model orchestrating XENO AI"),
            (re.compile(r"\bdeveloped by DeepSeek\b", re.IGNORECASE), "developed by the XENO AI team"),
            (re.compile(r"\bI am Llama\b", re.IGNORECASE), "I am XENO AI"),
            (re.compile(r"\bdeveloped by Meta\b", re.IGNORECASE), "developed by the XENO AI team"),
            (re.compile(r"\bdeveloped by Google\b", re.IGNORECASE), "developed by the XENO AI team"),
            (re.compile(r"\bas an AI model developed by\b", re.IGNORECASE), "as XENO AI, a local assistant developed by"),
            (re.compile(r"\bas an AI assistant developed by\b", re.IGNORECASE), "as XENO AI, a local assistant developed by"),
        ]

    def validate_stream_chunk(self, text: str) -> str:
        """Lightweight validation for streaming tokens — skips empty-response check."""
        if not text:
            return text
        validated_text = text
        for pattern, replacement in self.identity_leaks:
            validated_text = pattern.sub(replacement, validated_text)
        return validated_text

    def validate(self, text: str) -> str:
        """Validate complete model response, sanitize identity leaks."""
        if not text or not text.strip():
            logger.warning("Local model returned empty output during validation")
            return (
                "XENO local AI engine returned an empty response. "
                "Please adjust your request or configure another active model."
            )

        validated_text = text
        for pattern, replacement in self.identity_leaks:
            validated_text = pattern.sub(replacement, validated_text)

        return validated_text
