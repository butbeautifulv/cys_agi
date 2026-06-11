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
from cys_core.registry.agents import AgentRegistry, get_agent_registry
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
        runtime: AgentRuntime | None = None,
        bus: SecureAgentBus | None = None,
        registry: AgentRegistry | None = None,
    ) -> None:
        self.runtime = runtime or get_runtime()
        self.registry = registry or get_agent_registry()
        self.bus = bus or build_agent_bus(self.registry)
        self.sandbox = get_sandbox_connector()
        self.queue = get_job_queue()
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
        run_id = job.job_id
        try:
            creds = await self.sandbox.acreate(run_id, job.persona)
            job.sandbox_id = creds.sandbox_id
            job.status = WorkerJobStatus.RUNNING

            raw_input = self._job_input(job)
            sanitized = self.sanitizer.sanitize(raw_input, source="external")
            session_id = f"worker:{job.persona}:{run_id}"

            result = await self.runtime.arun(job.persona, sanitized, session_id=session_id)

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
            return RunResult(
                job_id=job.job_id,
                persona=job.persona,
                success=True,
                finding=result,
                sandbox_id=creds.sandbox_id,
            )
        except SecurityViolation as exc:
            job.status = WorkerJobStatus.FAILED
            return RunResult(job_id=job.job_id, persona=job.persona, success=False, error=str(exc))
        except Exception as exc:
            self.bus.record_agent_failure(job.persona)
            job.status = WorkerJobStatus.FAILED
            return RunResult(job_id=job.job_id, persona=job.persona, success=False, error=str(exc))
        finally:
            await self.sandbox.adestroy(run_id)

    async def process_next(self) -> RunResult | None:
        raw = await self.queue.adequeue(timeout=0.0)
        if raw is None:
            return None
        job = WorkerJob.model_validate(raw)
        result = await self.run_job(job)
        if not result.success and hasattr(self.queue, "send_to_dlq"):
            await self.queue.send_to_dlq(raw, error=result.error)
        return result

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
        return self.enqueue_from_routing_sync(
            event_id,
            personas,
            playbook_id=playbook_id,
            payload=payload,
            correlation_id=correlation_id,
        )
