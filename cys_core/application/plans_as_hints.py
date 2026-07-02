from __future__ import annotations

from pathlib import Path

import yaml

from cys_core.application.runtime_config import get_use_dynamic_catalog
from cys_core.registry.product_context import default_agents_root
from cys_core.infrastructure.catalog.registry_factory import get_plan_catalog


def load_plan_hints(plans_dir: Path | None = None) -> list[dict]:
    """Load routing plans as conductor context hints (catalog when dynamic)."""
    if get_use_dynamic_catalog():
        entries = get_plan_catalog().load_active()
        if entries:
            return [{"plan_id": entry.id, "rules": entry.rules} for entry in entries]
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
