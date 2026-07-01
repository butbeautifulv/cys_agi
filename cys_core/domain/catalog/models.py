from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class CatalogSource(str, Enum):
    FILESYSTEM = "filesystem"
    API = "api"
    SEED = "seed"


class CapabilityBinding(BaseModel):
    capability_id: str
    capability_type: str  # tool | skill
    trust_tier: str = "builtin"


class AgentCatalogEntry(BaseModel):
    name: str
    description: str = ""
    role: str = "worker"
    output_schema: str | None = None
    tools: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    hitl_tools: dict[str, bool] = Field(default_factory=dict)
    trust_level: str = "internal"
    bus_recipients: list[str] = Field(default_factory=list)
    system_prompt: str = ""
    system_prompt_digest: str = ""
    profile_id: str = "cybersec-soc"
    version: int = 1
    source: CatalogSource = CatalogSource.FILESYSTEM
    enabled: bool = True
    tags: list[str] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ProfilePack(BaseModel):
    id: str
    name: str
    description: str = ""
    default_personas: list[str] = Field(default_factory=list)
    default_skills: list[str] = Field(default_factory=list)


class CatalogVersion(BaseModel):
    profile_id: str
    version: int = 1
    agent_count: int = 0
