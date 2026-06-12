from __future__ import annotations

import pytest

from interfaces.worker.orchestrator import WorkerOrchestrator


@pytest.mark.unit
def test_sequential_enqueue_sets_dependencies():
    orch = WorkerOrchestrator(persona="soc")
    jobs = orch._jobs_for_routing(
        "evt-1",
        ["soc", "network", "compliance"],
        sequential=True,
    )
    assert jobs[0].depends_on_persona == ""
    assert jobs[1].depends_on_persona == "soc"
    assert jobs[2].depends_on_persona == "network"
