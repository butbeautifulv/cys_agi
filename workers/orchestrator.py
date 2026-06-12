from __future__ import annotations

import json
import uuid
from typing import Any, Protocol

from cys_core.domain.security.agent_bus import AgentTrustLevel, SecureAgentBus
from cys_core.domain.security.exceptions import SecurityViolation
from cys_core.domain.security.factory import get_input_sanitizer, get_output_guardrails
from cys_core.domain.workers.models import RunResult, WorkerJob, WorkerJobStatus
from cys_core.infrastructure.bus_transport import get_bus_transport
from cys_core.infrastructure.queue import get_job_queue
from cys_core.infrastructure.sandbox import get_sandbox_connector
from config import settings
from control.job_store import get_job_store
from cys_core.observability.metrics import metrics
from cys_core.observability.tracing import bind_correlation_id, reset_correlation_id
from cys_core.domain.workers.budgets import enrich_job_budget
from cys_core.security.job_budget import JobBudgetExceeded, JobBudgetTracker
from tool_gateway.policy import clear_chain_state
from cys_core.registry.agents import AgentRegistry, get_agent_registry
from cys_core.registry.mcp_tools import mcp_tool_registry
from cys_core.registry.skills_tool import make_load_skill_tool
from cys_core.registry.schemas import schema_registry
from cys_core.runtime.agent import AgentRuntime, get_runtime

_TRUST_MAP = {
    "untrusted": AgentTrustLevel.UNTRUSTED,
    "internal": AgentTrustLevel.INTERNAL,
    "privileged": AgentTrustLevel.PRIVILEGED,
    "system": AgentTrustLevel.SYSTEM,
}


class AgentRunner(Protocol):
    async def arun(self, name: str, user_input: str, *, session_id: str | None = None) -> dict[str, Any]: ...


def build_agent_bus(registry: AgentRegistry | None = None, signing_key: bytes = b"cys-agi-bus-key") -> SecureAgentBus:
    reg = registry or get_agent_registry()
    bus = SecureAgentBus(signing_key=signing_key)
    for defn in reg.all():
        bus.register_agent(
            defn.name,
            _TRUST_MAP.get(defn.trust_level, AgentTrustLevel.INTERNAL),
            defn.bus_recipients,
        )
    return bus


class WorkerOrchestrator:
    """Dequeue → sandbox → agent run → bus publish → sandbox destroy."""

    def __init__(
        self,
        *,
        persona: str | None = None,
        runtime: AgentRuntime | None = None,
        bus: SecureAgentBus | None = None,
        registry: AgentRegistry | None = None,
    ) -> None:
        self.persona = persona
        self.runtime = runtime or get_runtime()
        self.registry = registry or get_agent_registry()
        self.bus = bus or build_agent_bus(self.registry)
        self.sandbox = get_sandbox_connector()
        self.queue = get_job_queue(persona=persona)
        self.transport = get_bus_transport()
        self.sanitizer = get_input_sanitizer()
        self.guardrails = get_output_guardrails()

    def _job_input(self, job: WorkerJob) -> str:
        return json.dumps(
            {
                "event_id": job.event_id,
                "playbook_id": job.playbook_id,
                "payload": job.payload,
                "sandbox_id": job.sandbox_id,
                "feedback": job.feedback,
            },
            ensure_ascii=False,
        )

    async def run_job(self, job: WorkerJob) -> RunResult:
        budgeted = enrich_job_budget(job)
        run_id = job.job_id
        session_id = f"worker:{job.persona}:{run_id}"
        cid_token = bind_correlation_id(job.correlation_id or job.event_id)
        JobBudgetTracker.configure(
            session_id,
            max_tokens=budgeted.max_tokens,
            max_cost_usd=budgeted.max_cost_usd,
            max_tool_calls=budgeted.max_tool_calls,
        )
        try:
            with metrics.track_worker_job(job.persona) as job_state:
                return await self._run_job_inner(job, budgeted, session_id, job_state)
        finally:
            state = JobBudgetTracker.get(session_id)
            if state is not None:
                metrics.record_job_usage(
                    job.persona,
                    tokens=state.tokens_used,
                    cost_usd=state.cost_usd,
                )
            JobBudgetTracker.clear(session_id)
            clear_chain_state(job.job_id)
            reset_correlation_id(cid_token)

    async def _run_job_inner(
        self,
        job: WorkerJob,
        budgeted: WorkerJob,
        session_id: str,
        job_state: dict[str, str],
    ) -> RunResult:
        run_id = job.job_id
        try:
            creds = await self.sandbox.acreate(run_id, job.persona)
            job.sandbox_id = creds.sandbox_id
            job.status = WorkerJobStatus.RUNNING
            get_job_store().upsert_running(job.job_id, session_id, job.persona)

            raw_input = self._job_input(job)
            sanitized = self.sanitizer.sanitize(raw_input, source="external")
            defn = self.registry.get(job.persona)
            sandbox_tools: list = []
            if settings.use_tool_gateway:
                sandbox_tools.extend(
                    mcp_tool_registry.resolve(
                        defn.tools,
                        creds.sandbox_id,
                        persona=job.persona,
                        job_id=job.job_id,
                        correlation_id=job.correlation_id,
                    )
                )
            else:
                from cys_core.registry.tools import tool_registry

                sandbox_tools.extend(tool_registry.resolve(defn.tools))
            if defn.skills:
                sandbox_tools.append(
                    make_load_skill_tool(defn.skills, persona=job.persona, job_id=job.job_id)
                )

            result = await self.runtime.arun(
                job.persona,
                sanitized,
                session_id=session_id,
                sandbox_tools=sandbox_tools or None,
                job_id=job.job_id,
                event_id=job.event_id,
                correlation_id=job.correlation_id,
                sandbox_id=creds.sandbox_id,
            )

            schema = schema_registry.get(self.registry.get(job.persona).schema_name or "")
            if schema and "error" not in result:
                validated = self.guardrails.validate_schema(result, schema)
                result = validated.model_dump()

            envelope = self.bus.send_message(
                job.persona,
                "critic",
                "finding",
                {"agent": job.persona, "event_id": job.event_id, "data": result, "sandbox_id": creds.sandbox_id},
            )
            self.bus.receive_message("critic", envelope)
            await self.transport.publish("critic", envelope)
            await self.transport.publish("coordinator", envelope)

            job.status = WorkerJobStatus.COMPLETED
            get_job_store().mark_completed(job.job_id)
            return RunResult(
                job_id=job.job_id,
                persona=job.persona,
                success=True,
                finding=result,
                sandbox_id=creds.sandbox_id,
            )
        except JobBudgetExceeded as exc:
            job_state["status"] = "error"
            job.status = WorkerJobStatus.FAILED
            get_job_store().mark_failed(job.job_id)
            return RunResult(job_id=job.job_id, persona=job.persona, success=False, error=str(exc))
        except SecurityViolation as exc:
            job_state["status"] = "error"
            metrics.record_sanitizer_block("worker", "hard")
            job.status = WorkerJobStatus.FAILED
            get_job_store().mark_failed(job.job_id)
            return RunResult(job_id=job.job_id, persona=job.persona, success=False, error=str(exc))
        except Exception as exc:
            job_state["status"] = "error"
            self.bus.record_agent_failure(job.persona)
            job.status = WorkerJobStatus.FAILED
            get_job_store().mark_failed(job.job_id)
            send_dlq = getattr(self.queue, "send_to_dlq", None)
            if send_dlq is not None:
                await send_dlq(job.model_dump(), str(exc))
            return RunResult(job_id=job.job_id, persona=job.persona, success=False, error=str(exc))
        finally:
            await self.sandbox.adestroy(run_id)

    async def process_next(self) -> RunResult | None:
        raw = await self.queue.adequeue(timeout=0.0)
        if raw is None:
            return None
        job = WorkerJob.model_validate(raw)
        return await self.run_job(job)

    def enqueue_from_routing_sync(
        self,
        event_id: str,
        personas: list[str],
        *,
        playbook_id: str = "",
        payload: dict[str, Any] | None = None,
        correlation_id: str = "",
    ) -> list[str]:
        job_ids: list[str] = []
        for persona in personas:
            job_id = f"{persona}-{event_id}-{uuid.uuid4().hex[:8]}"
            job = WorkerJob(
                job_id=job_id,
                event_id=event_id,
                persona=persona,
                playbook_id=playbook_id,
                payload=payload or {},
                correlation_id=correlation_id or event_id,
            )
            self.queue.enqueue(job.model_dump())
            job_ids.append(job_id)
        return job_ids

    async def enqueue_from_routing(
        self,
        event_id: str,
        personas: list[str],
        *,
        playbook_id: str = "",
        payload: dict[str, Any] | None = None,
        correlation_id: str = "",
    ) -> list[str]:
        job_ids: list[str] = []
        for persona in personas:
            job_id = f"{persona}-{event_id}-{uuid.uuid4().hex[:8]}"
            job = WorkerJob(
                job_id=job_id,
                event_id=event_id,
                persona=persona,
                playbook_id=playbook_id,
                payload=payload or {},
                correlation_id=correlation_id or event_id,
            )
            await self.queue.aenqueue(job.model_dump())
            job_ids.append(job_id)
        return job_ids
