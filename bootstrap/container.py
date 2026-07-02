from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING, Any

from bootstrap.settings import Settings, get_settings
from cys_core.application.policy_enforcement import PolicyEnforcementService
from cys_core.application.policy_resolver import (
    ProfilePolicyResolver,
    configure_policy_resolver_from_settings,
)
from cys_core.application.runtime_config import configure_from_settings
from cys_core.domain.catalog.profile_id import DEFAULT_PROFILE_ID
from cys_core.infrastructure.catalog.hybrid_registry import get_agent_catalog, reload_agent_registry
from cys_core.infrastructure.catalog.profile_policy import (
    ProfilePolicyLoader,
    get_breaker_config,
    get_bus_policy,
    get_cost_per_1k_tokens,
    get_escalation_paths,
    get_hitl_threshold,
    get_max_spawn_depth,
    get_notify_control_severities,
    get_profile_policy,
    get_trust_floor,
)
from cys_core.infrastructure.catalog.registry_factory import (
    get_catalog_audit,
    get_catalog_write_gate,
    get_mcp_catalog,
    get_plan_catalog,
    get_skill_catalog,
    get_tool_catalog,
)

if TYPE_CHECKING:
    from cys_core.application.ports import PersistenceContext
    from cys_core.application.ports.bus import AgentTransportConnector
    from cys_core.application.ports.job_queue import JobQueueConnector
    from cys_core.application.ports.memory import EpisodicMemoryStore, InvestigationStateStore
    from cys_core.application.ports.sandbox import SandboxConnector


class Container:
    """Composition root for infrastructure connectors, catalog ports, and policy wiring."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        configure_from_settings(self.settings)
        self._policy_loader = ProfilePolicyLoader(get_agent_catalog)
        self._resolver = configure_policy_resolver_from_settings(
            self.settings,
            policy_loader=self._policy_loader,
        )
        self._enforcement = PolicyEnforcementService(self._resolver)

    def get_job_queue(self, persona: str | None = None) -> JobQueueConnector:
        from cys_core.infrastructure.queue import get_job_queue

        return get_job_queue(persona=persona, settings=self.settings)

    def get_bus_transport(self) -> AgentTransportConnector:
        from cys_core.infrastructure.bus_transport import get_bus_transport

        return get_bus_transport(settings=self.settings)

    def get_sandbox_connector(self) -> SandboxConnector:
        from cys_core.infrastructure.sandbox import get_sandbox_connector

        return get_sandbox_connector(settings=self.settings)

    def get_persistence_context(self) -> PersistenceContext:
        from cys_core.persistence import get_persistence_connector

        return get_persistence_connector(self.settings.persistence_connector).open()

    async def get_async_persistence_context(self) -> PersistenceContext:
        from cys_core.persistence import get_persistence_connector

        connector = get_persistence_connector(self.settings.persistence_connector)
        return await connector.open_async()

    def get_job_store(self):
        from interfaces.control_plane.job_store import get_job_store

        return get_job_store(self.settings)

    def get_episodic_memory_store(self) -> EpisodicMemoryStore:
        from cys_core.infrastructure.memory.factory import get_episodic_memory_store

        return get_episodic_memory_store(settings=self.settings)

    def get_investigation_state_store(self) -> InvestigationStateStore:
        from cys_core.infrastructure.memory.factory import get_investigation_state_store

        return get_investigation_state_store(settings=self.settings)

    def get_trace_backend(self):
        from bootstrap.observability_factory import build_trace_backend, resolve_trace_backend_name

        return build_trace_backend(resolve_trace_backend_name(self.settings), cfg=self.settings)

    def get_prompt_backend(self):
        from bootstrap.observability_factory import build_prompt_backend

        return build_prompt_backend(self.settings.obs_prompt_backend)

    def get_judge_backend(self):
        from bootstrap.observability_factory import build_judge_backend

        name = "langfuse" if self.settings.critic_use_llm_judge else self.settings.obs_judge_backend
        return build_judge_backend(name)

    def get_eval_backend(self):
        from bootstrap.observability_factory import build_eval_backend

        return build_eval_backend(self.settings.obs_eval_backend)

    def get_prompt_resolver(self):
        from cys_core.application.observability.prompt_resolver import PromptResolver

        return PromptResolver(self.get_prompt_backend())

    def get_token_verifier(self):
        from cys_core.infrastructure.auth.factory import build_token_verifier

        return build_token_verifier(self.settings)

    def get_agent_catalog(self):
        return get_agent_catalog()

    def get_skill_catalog(self):
        return get_skill_catalog()

    def get_plan_catalog(self):
        return get_plan_catalog()

    def get_mcp_catalog(self):
        return get_mcp_catalog()

    def get_tool_catalog(self):
        return get_tool_catalog()

    def get_catalog_write_gate(self):
        return get_catalog_write_gate()

    def get_catalog_audit(self):
        return get_catalog_audit()

    def get_profile_policy_port(self) -> ProfilePolicyLoader:
        return self._policy_loader

    def get_policy_resolver(self) -> ProfilePolicyResolver:
        return self._resolver

    def get_policy_enforcement(self) -> PolicyEnforcementService:
        return self._enforcement

    def reload_catalog(self) -> None:
        reload_agent_registry()

    def wire_hitl_pause(self) -> None:
        from cys_core.infrastructure.kafka_paused import publish_paused_job_sync
        from cys_core.middleware import hitl_pause
        from cys_core.observability.metrics import metrics

        store = self.get_job_store()

        class _JobStoreHitlAdapter:
            def pause_for_hitl(self, pending: Any, preview: dict[str, Any]) -> None:
                store.pause_for_hitl(pending, preview)

            def list_pending_approvals(self) -> list[Any]:
                return store.list_pending_approvals()

        hitl_pause.configure(
            registry=_JobStoreHitlAdapter(),
            publish_paused=publish_paused_job_sync,
            on_pause_count=lambda count: metrics.refresh_hitl_pending(count),
        )

    def wire_tool_backend(self) -> None:
        from cys_core.registry.tools import configure_tool_backend
        from interfaces.gateways.tool.adapters.rag import rag_query_tool
        from interfaces.gateways.tool.adapters.siem import query_siem_readonly_search

        class _GatewayToolBackend:
            def query_siem(self, query: str, time_range: str = "24h") -> dict[str, Any]:
                return query_siem_readonly_search(query=query, time_range=time_range)

            def rag_query(self, query: str, persona: str = "soc", tenant: str = "default") -> dict[str, Any]:
                return rag_query_tool(query=query, persona=persona, tenant=tenant)

        configure_tool_backend(_GatewayToolBackend())

    def wire_bus_reload(self) -> None:
        from cys_core.infrastructure.catalog.hybrid_registry import register_bus_reload_callback
        from interfaces.worker.orchestrator import build_agent_bus

        register_bus_reload_callback(build_agent_bus)

    def wire_agent_definitions_loader(self) -> None:
        from bootstrap.agent_definitions_loader import get_default_agent_definitions_loader
        from bootstrap.otel_wiring import wire_otel
        from cys_core.application.ports.persistence_provider import configure_persistence_providers
        from cys_core.application.ports.trace_callbacks import configure_trace_callbacks
        from cys_core.infrastructure.catalog.hybrid_registry import register_definitions_loader
        from cys_core.observability.langfuse_client import configure_trace_backend_factory
        from cys_core.registry.agents import configure_agent_definitions_loader

        wire_otel()
        configure_persistence_providers(self.get_persistence_context, self.get_async_persistence_context)

        def _trace_callbacks():
            handler = self.get_trace_backend().get_callback_handler()
            return [handler] if handler is not None else []

        configure_trace_callbacks(_trace_callbacks)
        configure_trace_backend_factory(self.get_trace_backend)
        loader = get_default_agent_definitions_loader()
        configure_agent_definitions_loader(loader)
        register_definitions_loader(loader)


@lru_cache
def get_container() -> Container:
    container = Container()
    container.wire_hitl_pause()
    container.wire_tool_backend()
    container.wire_agent_definitions_loader()
    container.wire_bus_reload()
    return container


__all__ = [
    "DEFAULT_PROFILE_ID",
    "Container",
    "get_agent_catalog",
    "get_breaker_config",
    "get_bus_policy",
    "get_container",
    "get_cost_per_1k_tokens",
    "get_escalation_paths",
    "get_hitl_threshold",
    "get_max_spawn_depth",
    "get_notify_control_severities",
    "get_profile_policy",
    "get_trust_floor",
]
