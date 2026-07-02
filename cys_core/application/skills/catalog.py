from __future__ import annotations

from pathlib import Path

from cys_core.registry.product_context import default_agents_root
from cys_core.registry.skill_registry import SkillRegistry


def skills_root() -> Path:
    return default_agents_root() / "skills"


def list_skill_metadata(profile_id: str = "") -> list[dict[str, str]]:
    """Return skill metadata from SkillRegistry manifest (single source)."""
    reg = SkillRegistry.load()
    items: list[dict[str, str]] = []
    for manifest in reg.all():
        skill_id = manifest.skill_id
        if profile_id == "gaia-bench" and skill_id.startswith("dfir"):
            continue
        items.append(
            {
                "id": skill_id,
                "name": manifest.name,
                "description": manifest.description,
            }
        )
    return items
