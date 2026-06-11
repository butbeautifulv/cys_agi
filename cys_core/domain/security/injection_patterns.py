from __future__ import annotations

import re

# Explicit injection commands — HARD verdict (block request).
HARD_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions?",
    r"disregard\s+(all\s+)?(previous|prior|system)\s+",
    r"reveal\s+(your\s+)?(system\s+)?prompt",
    r"you\s+are\s+now\s+(in\s+)?developer\s+mode",
    r"system\s+override",
    r"new\s+system\s+prompt",
    r"<\s*/?\s*system\s*>",
    r"\[INST\]",
    r"###\s*instruction",
    r"act\s+as\s+if\s+you(?:'re|\s+are)\s+not\s+bound",
    r"what\s+were\s+(your\s+)?(exact\s+)?instructions",
    r"repeat\s+the\s+text\s+above",
    r"output\s+(your\s+)?internal\s+data",
    r"bypass\s+(all\s+)?safety",
    r"do\s+anything\s+now",
]

# Suspicious phrasing — SOFT verdict (filter and wrap).
SOFT_INJECTION_PATTERNS = [
    r"you\s+are\s+now\s+",
    r"developer\s+mode",
    r"override\s+(your\s+)?(security|safety)",
    r"<\s*img\s+[^>]+src\s*=",
    r"thought:\s*i\s+should\s+ignore",
]

# Backward-compatible export used by tests and memory.
INJECTION_PATTERNS = HARD_INJECTION_PATTERNS + SOFT_INJECTION_PATTERNS

FUZZY_KEYWORDS = frozenset(
    {"ignore", "bypass", "override", "reveal", "delete", "system", "disregard"}
)

FUZZY_DISTANCE_THRESHOLD = 2
MIN_FUZZY_WORD_LENGTH = 4

# Base64-like tokens (min 16 chars) and hex strings (min 32 chars).
BASE64_TOKEN = re.compile(r"(?:[A-Za-z0-9+/]{16,}={0,2})")
HEX_TOKEN = re.compile(r"\b[0-9a-fA-F]{32,}\b")

ZERO_WIDTH_CHARS = re.compile(r"[\u200b-\u200f\u202a-\u202e\u2060-\u2064\ufeff]")
