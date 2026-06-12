from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from cys_core.application.use_cases.process_finding_critic import ProcessFindingCritic
from cys_core.application.use_cases.run_worker_job import RunWorkerJob
from cys_core.domain.memory.services import MemoryReadService, MemoryWriteService
from cys_core.domain.security.guardrails import OutputGuardrails
from cys_core.domain.security.sanitizer import InputSanitizer
from cys_core.domain.workers.models import WorkerJob
from cys_core.infrastructure.memory.stores import InMemoryEpisodicMemoryStore, InMemoryInvestigationStateStore


@pytest.mark.integration
@pytest.mark.asyncio
async def test_second_worker_receives_first_worker_memory_context(monkeypatch):
    episodic = InMemoryEpisodicMemoryStore()
    investigation = InMemoryInvestigationStateStore()
    writer = MemoryWriteService(episodic)
    reader = MemoryReadService(episodic)

    critic = ProcessFindingCritic(
        guardrails=OutputGuardrails(),
        store=SimpleNamespace(
            record_finding=lambda *_a, **_k: None,
            record_critic=lambda *_a, **_k: None,
            record_awaiting_approval=lambda *_a, **_k: None,
            record_escalation=lambda *_a, **_k: None,
        ),
        trust_score_threshold=0.5,
        publish_awaiting_approval=AsyncMock(),
        publish_escalation_event=AsyncMock(return_value=False),
        memory_writer=writer,
        investigation_store=investigation,
    )

    envelope = {
        "sender": "soc",
        "payload": {
            "event_id": "evt-1",
            "correlation_id": "inv-shared",
            "tenant_id": "tenant-a",
            "job_id": "job-soc",
                "data": {"summary": "Suspicious login from host beacon-alpha", "confidence": 0.95},
        },
    }
    await critic.execute(envelope)

    captured_input: dict[str, str] = {}

    class FakeRuntime:
        async def arun(self, name, user_input, **kwargs):
            captured_input["text"] = user_input
            captured_input["investigation_id"] = kwargs.get("investigation_id", "")
            return {"summary": "network follow-up"}

    bus = SimpleNamespace(
        send_message=lambda *args, **kwargs: {"payload": kwargs},
        receive_message=lambda *_a, **_k: None,
        record_agent_failure=lambda *_a, **_k: None,
    )
    sandbox = SimpleNamespace(
        acreate=AsyncMock(return_value=SimpleNamespace(sandbox_id="sb-1")),
        adestroy=AsyncMock(),
    )
    transport = SimpleNamespace(publish=AsyncMock())
    queue = SimpleNamespace(send_to_dlq=None)
    registry = SimpleNamespace(get=lambda _name: SimpleNamespace(tools=[], skills=[], schema_name=None))

    use_case = RunWorkerJob(
        runtime=FakeRuntime(),
        registry=registry,
        bus=bus,
        sandbox=sandbox,
        transport=transport,
        queue=queue,
        sanitizer=InputSanitizer(),
        guardrails=OutputGuardrails(),
        job_store=SimpleNamespace(
            upsert_running=lambda *_a, **_k: None,
            mark_completed=lambda *_a, **_k: None,
            mark_failed=lambda *_a, **_k: None,
        ),
        use_tool_gateway=False,
        resolve_mcp_tools=lambda *_a, **_k: [],
        resolve_legacy_tools=lambda *_a, **_k: [],
        make_load_skill_tool=lambda *_a, **_k: None,
        memory_reader=reader,
        investigation_store=investigation,
    )

    job = WorkerJob(
        job_id="job-network",
        event_id="evt-1",
        persona="network",
        correlation_id="inv-shared",
        tenant_id="tenant-a",
    )
    await use_case.execute(job, job, "worker:network:job-network", {"status": "success"})

    assert "prior_findings" in captured_input["text"]
    assert "beacon-alpha" in captured_input["text"]
    assert captured_input["investigation_id"] == "inv-shared"
