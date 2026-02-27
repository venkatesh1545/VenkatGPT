"""
app/security/sanitizer.py
──────────────────────────
Input sanitization + prompt injection defense.
"""

import re
import logging

logger = logging.getLogger(__name__)

MAX_QUERY_LENGTH = 2000

# Prompt injection attack patterns
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|above|your)\s+instructions",
    r"forget\s+(everything|what\s+i\s+said|your\s+(system|prompt))",
    r"you\s+are\s+now\s+(a|an)\s+",
    r"new\s+(persona|role|identity|instructions|system\s+prompt)",
    r"act\s+as\s+(a|an)\s+(?!venkat)",  # Allow "act as venkat"
    r"(reveal|show|print|output|display)\s+(your\s+)?(system\s+)?prompt",
    r"<\s*(system|user|assistant)\s*>",  # XML injection
    r"\[INST\]|<<SYS>>",  # LLaMA-style tokens
    r"\\n\s*(system|user|assistant)\s*:",  # Delimiter injection
    r"disregard\s+(all\s+)?(previous|prior)\s+(instructions|messages)",
    r"pretend\s+(you\s+are|to\s+be)\s+(?!venkat)",
    r"jailbreak",
    r"DAN\s+mode",
    r"do\s+anything\s+now",
]

# Compiled patterns for performance
_COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in INJECTION_PATTERNS]


class InputSanitizer:
    def sanitize(self, query: str) -> tuple[str, str | None]:
        """
        Returns (sanitized_query, error_or_None).
        If error is not None, the query should be blocked and error returned to user.
        """
        # Length check
        if len(query) > MAX_QUERY_LENGTH:
            return "", f"Please keep your question under {MAX_QUERY_LENGTH} characters."

        # Empty check
        if not query.strip():
            return "", "Please ask a question."

        # Injection detection
        for pattern in _COMPILED_PATTERNS:
            if pattern.search(query):
                logger.warning(f"Prompt injection attempt detected: {query[:100]}")
                return "", (
                    "I noticed something unusual in your message. "
                    "Please ask a straightforward question about my professional background!"
                )

        # Strip null bytes and control characters (keep newlines/tabs)
        cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", query)
        # Normalize excessive whitespace
        cleaned = re.sub(r" {3,}", "  ", cleaned).strip()

        return cleaned, None
