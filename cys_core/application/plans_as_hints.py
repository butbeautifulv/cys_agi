from __future__ import annotations

from pathlib import Path

import yaml

from cys_core.registry.product_context import default_agents_root


def load_plan_hints(plans_dir: Path | None = None) -> list[dict]:
    """Load routing plans as conductor context hints (not sole router)."""
    base = plans_dir or (default_agents_root() / "plans")
    hints: list[dict] = []
    if not base.is_dir():
        return hints
    for path in sorted(base.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        routing = data.get("routing", data)
        rules = routing.get("rules", []) if isinstance(routing, dict) else []
        hints.append({"plan_id": data.get("id", path.stem), "rules": rules})
    return hints
