from __future__ import annotations

import json
from typing import Any


def coerce_tool_args(args: dict[str, Any]) -> dict[str, Any]:
    """Normalize LLM tool args (string ints/bools/lists) before execution."""
    out: dict[str, Any] = {}
    for key, value in args.items():
        out[key] = _coerce_value(value)
    return out


def _coerce_value(value: Any) -> Any:
    if isinstance(value, str):
        stripped = value.strip()
        lower = stripped.lower()
        if lower in ("true", "false"):
            return lower == "true"
        if stripped.isdigit():
            return int(stripped)
        if stripped.startswith("[") or stripped.startswith("{"):
            try:
                return json.loads(stripped)
            except json.JSONDecodeError:
                return value
    if isinstance(value, dict):
        return {k: _coerce_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_coerce_value(item) for item in value]
    return value
