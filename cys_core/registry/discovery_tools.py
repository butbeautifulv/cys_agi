from __future__ import annotations

from cys_core.application.ports.catalog import AgentCatalogPort
from cys_core.domain.runs.mode_policy import ModePolicy
from cys_core.domain.runs.models import InteractionMode
from cys_core.registry.agents import AgentRegistry
from cys_core.registry.skill_registry import SkillRegistry
from cys_core.registry.tools import tool_registry


def search_personas(query: str, *, catalog: AgentCatalogPort | None = None, limit: int = 5) -> list[dict]:
    registry = AgentRegistry.load()
    names = registry.names()
    q = query.lower()
    hits = [name for name in names if q in name or q in registry.get(name).description.lower()]
    return [{"name": name, "description": registry.get(name).description} for name in hits[:limit]]


def search_skills(query: str, *, limit: int = 5) -> list[dict]:
    reg = SkillRegistry.load()
    q = query.lower()
    hits = [sid for sid in reg.names() if q in sid or q in (reg.get(sid).description or "").lower()]
    return [{"id": sid, "description": reg.get(sid).description} for sid in hits[:limit]]


def search_tools(query: str, *, mode: InteractionMode | None = None, limit: int = 10) -> list[dict]:
    q = query.lower()
    names = tool_registry.names()
    hits = [name for name in names if q in name]
    allowed = [name for name in hits if ModePolicy.allow_tool(mode, name)]
    return [{"name": name} for name in allowed[:limit]]
