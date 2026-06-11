from __future__ import annotations

import re
from typing import Any

PII_PATTERNS: list[tuple[str, str]] = [
    (r"\b\d{3}-\d{2}-\d{4}\b", "[SSN_REDACTED]"),
    (r"\b\d{16}\b", "[CARD_REDACTED]"),
    (r"password\s*[:=]\s*\S+", "password=[REDACTED]"),
    (r"api[_-]?key\s*[:=]\s*\S+", "api_key=[REDACTED]"),
    (r"secret\s*[:=]\s*\S+", "secret=[REDACTED]"),
    (r"token\s*[:=]\s*\S+", "token=[REDACTED]"),
]

SENSITIVE_KEYS = frozenset({"password", "api_key", "token", "secret", "credential"})


class RedactionService:
    """PII and sensitive-key redaction policies."""

    def redact_pii(self, text: str) -> str:
        for pattern, replacement in PII_PATTERNS:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        return text

    def redact_sensitive_keys(self, data: Any) -> Any:
        if isinstance(data, dict):
            return {
                k: "***REDACTED***" if k.lower() in SENSITIVE_KEYS else self.redact_sensitive_keys(v)
                for k, v in data.items()
            }
        if isinstance(data, list):
            return [self.redact_sensitive_keys(item) for item in data]
        return data

    def contains_sensitive_data(self, text: str) -> bool:
        patterns = (
            r"\b\d{3}-\d{2}-\d{4}\b",
            r"\b\d{16}\b",
            r"password\s*[:=]\s*\S+",
            r"api[_-]?key\s*[:=]\s*\S+",
        )
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)
