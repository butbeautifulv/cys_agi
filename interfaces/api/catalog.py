from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from bootstrap.catalog_loader import load_profile_pack
from cys_core.application.use_cases.seed_catalog import SeedCatalog
from cys_core.application.use_cases.upsert_catalog_agent import UpsertCatalogAgent
from cys_core.domain.security.auth_models import AuthClaims
from cys_core.infrastructure.catalog.audit import list_catalog_audit
from cys_core.infrastructure.catalog.audit_adapter import InMemoryCatalogAudit
from cys_core.infrastructure.catalog.hybrid_registry import get_agent_catalog, reload_agent_registry
from interfaces.api.auth import require_operator_role, require_reader_role

router = APIRouter(prefix="/catalog", tags=["catalog"])


class AgentCatalogOut(BaseModel):
    name: str
    description: str = ""
    role: str = ""
    output_schema: str | None = None
    tools: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    profile_id: str = ""
    version: int = 1
    enabled: bool = True


class AgentCatalogPut(BaseModel):
    description: str = ""
    role: str = "worker"
    output_schema: str | None = None
    tools: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    trust_level: str = "internal"
    bus_recipients: list[str] = Field(default_factory=list)
    enabled: bool = True
    profile_id: str = "cybersec-soc"


def _entry_out(entry) -> AgentCatalogOut:
    return AgentCatalogOut(
        name=entry.name,
        description=entry.description,
        role=entry.role,
        output_schema=entry.output_schema,
        tools=entry.tools,
        skills=entry.skills,
        profile_id=entry.profile_id,
        version=entry.version,
        enabled=entry.enabled,
    )


@router.get("/agents")
async def list_agents(
    profile_id: str | None = None,
    _auth: Annotated[AuthClaims | None, Depends(require_reader_role)] = None,
) -> dict[str, Any]:
    agents = get_agent_catalog().list_agents(profile_id=profile_id)
    return {"agents": [_entry_out(a).model_dump() for a in agents]}


@router.get("/agents/{name}")
async def get_agent(
    name: str,
    _auth: Annotated[AuthClaims | None, Depends(require_reader_role)] = None,
) -> AgentCatalogOut:
    entry = get_agent_catalog().get_agent(name)
    if entry is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return _entry_out(entry)


@router.put("/agents/{name}")
async def put_agent(
    name: str,
    body: AgentCatalogPut,
    _auth: Annotated[AuthClaims | None, Depends(require_operator_role)] = None,
) -> AgentCatalogOut:
    saved = UpsertCatalogAgent(
        get_agent_catalog(),
        reload=reload_agent_registry,
        record_audit=InMemoryCatalogAudit().record_change,
    ).execute(
        name,
        body.model_dump(),
        actor=getattr(_auth, "sub", "api") if _auth else "api",
    )
    return _entry_out(saved)


@router.get("/profiles")
async def list_profiles(
    _auth: Annotated[AuthClaims | None, Depends(require_reader_role)] = None,
) -> dict[str, Any]:
    catalog = get_agent_catalog()
    profiles = catalog.list_profiles()
    return {"profiles": [p.model_dump() if hasattr(p, "model_dump") else p for p in profiles]}


@router.get("/audit")
async def catalog_audit(
    limit: int = 50,
    _auth: Annotated[AuthClaims | None, Depends(require_reader_role)] = None,
) -> dict[str, Any]:
    return {"entries": list_catalog_audit(limit=limit)}


@router.post("/seed")
async def seed_catalog(
    _auth: Annotated[AuthClaims | None, Depends(require_operator_role)] = None,
) -> dict[str, Any]:
    return SeedCatalog(
        get_agent_catalog(),
        load_profile_pack=load_profile_pack,
        reload=reload_agent_registry,
    ).execute()
