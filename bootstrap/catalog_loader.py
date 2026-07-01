from __future__ import annotations

from bootstrap.product_loader import load_agent_definitions
from cys_core.domain.agents.models import AgentDefinition
from cys_core.domain.catalog.models import AgentCatalogEntry, CatalogSource, ProfilePack

DEFAULT_PROFILE_ID = "cybersec-soc"


def entry_to_definition(entry: AgentCatalogEntry) -> AgentDefinition:
    return AgentDefinition(
        name=entry.name,
        description=entry.description,
        role=entry.role,  # type: ignore[arg-type]
        system_prompt=entry.system_prompt,
        system_prompt_digest=entry.system_prompt_digest,
        schema_name=entry.output_schema,
        tools=entry.tools,
        skills=entry.skills,
        hitl_tools=entry.hitl_tools,
        trust_level=entry.trust_level,
        bus_recipients=entry.bus_recipients,
    )


def definition_to_entry(defn: AgentDefinition, *, profile_id: str = DEFAULT_PROFILE_ID) -> AgentCatalogEntry:
    return AgentCatalogEntry(
        name=defn.name,
        description=defn.description,
        role=defn.role,
        output_schema=defn.schema_name,
        tools=defn.tools,
        skills=defn.skills,
        hitl_tools=defn.hitl_tools,
        trust_level=defn.trust_level,
        bus_recipients=defn.bus_recipients,
        system_prompt=defn.system_prompt,
        system_prompt_digest=defn.system_prompt_digest,
        profile_id=profile_id,
        source=CatalogSource.FILESYSTEM,
        enabled=True,
    )


def load_profile_pack() -> tuple[ProfilePack, list[AgentCatalogEntry]]:
    agents = load_agent_definitions()
    workers = [a for a in agents.values() if a.role in ("worker", "specialist")]
    profile = ProfilePack(
        id=DEFAULT_PROFILE_ID,
        name="Cybersec SOC",
        description="Filesystem personas from agents/personas/",
        default_personas=[a.name for a in workers],
    )
    entries = [definition_to_entry(defn) for defn in agents.values()]
    return profile, entries
