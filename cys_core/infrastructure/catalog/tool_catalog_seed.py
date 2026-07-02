from __future__ import annotations

from cys_core.domain.catalog.models import CatalogSource, ToolCatalogEntry
from cys_core.domain.security.risk import ACTION_RISK_MAPPING
from cys_core.registry.tools import _BUILTIN_TOOL_NAMES
from cys_core.registry.veil_tools import _VEIL_TOOL_DESCRIPTIONS


def load_tools_for_seed(profile_id: str = "cybersec-soc") -> list[ToolCatalogEntry]:
    entries: list[ToolCatalogEntry] = []
    for name in _BUILTIN_TOOL_NAMES:
        risk = ACTION_RISK_MAPPING.get(name)
        entries.append(
            ToolCatalogEntry(
                id=name,
                profile_id=profile_id,
                name=name,
                description="",
                risk_tier=risk or "medium",
                handler="builtin",
                source=CatalogSource.SEED,
            )
        )
    for name, description in _VEIL_TOOL_DESCRIPTIONS.items():
        entries.append(
            ToolCatalogEntry(
                id=name,
                profile_id=profile_id,
                name=name,
                description=description,
                risk_tier="low",
                handler="veil",
                source=CatalogSource.SEED,
            )
        )
    return entries
