from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

from cys_core.domain.security.factory import get_input_sanitizer
from cys_core.domain.security.redaction import RedactionService
from cys_core.domain.security.sanitizer import InjectionVerdict


class SecureAgentMemory:
    """Validated, isolated agent memory (cheat sheet §3)."""

    MAX_MEMORY_ITEMS = 100
    MAX_ITEM_LENGTH = 5000
    MEMORY_TTL_HOURS = 24

    def __init__(self, user_id: str, signing_key: bytes | None = None) -> None:
        self.user_id = user_id
        self.signing_key = signing_key or b"cys-agi-default-key"
        self.memories: list[dict] = []
        self._sanitizer = get_input_sanitizer()
        self._redaction = RedactionService()

    def add(self, content: str, memory_type: str = "conversation") -> None:
        if self._sanitizer.classify(content) is not InjectionVerdict.NONE:
            return
        if len(content) > self.MAX_ITEM_LENGTH:
            content = content[: self.MAX_ITEM_LENGTH]
        if self._redaction.contains_sensitive_data(content):
            content = self._redaction.redact_pii(content)
        content = self._sanitizer.filter_patterns(content)
        entry = {
            "content": content,
            "type": memory_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": self.user_id,
            "checksum": self._compute_checksum(content),
        }
        self.memories.append(entry)
        self._enforce_limits()

    def get_context(self) -> list[str]:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=self.MEMORY_TTL_HOURS)
        valid: list[str] = []
        for mem in self.memories:
            mem_time = datetime.fromisoformat(mem["timestamp"])
            if mem_time > cutoff and self._verify_checksum(mem):
                valid.append(mem["content"])
        return valid

    def _compute_checksum(self, content: str) -> str:
        return hashlib.sha256((content + self.user_id).encode() + self.signing_key).hexdigest()[:16]

    def _verify_checksum(self, entry: dict) -> bool:
        expected = self._compute_checksum(entry["content"])
        return entry.get("checksum") == expected

    def _enforce_limits(self) -> None:
        if len(self.memories) > self.MAX_MEMORY_ITEMS:
            self.memories = self.memories[-self.MAX_MEMORY_ITEMS :]
