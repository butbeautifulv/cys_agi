from __future__ import annotations

import pytest

from control.coordinator_service import CoordinatorService
from control.critic_service import CriticService
from control.status_store import StatusStore


@pytest.mark.unit
@pytest.mark.asyncio
async def test_critic_service_feedback():
    store = StatusStore()
    critic = CriticService()
    critic.store = store
    envelope = {
        "sender": "soc",
        "payload": {"event_id": "e1", "data": {"priority": "high", "confidence": 0.3}},
    }
    feedback = await critic.handle_message(envelope)
    assert feedback["trust_score"] == 0.3
    assert "high_severity" in feedback["issues_detected"]
    assert len(store.critic_feedback) == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_coordinator_service_narrative():
    store = StatusStore()
    coord = CoordinatorService()
    coord.store = store
    await coord.handle_message({"sender": "soc", "payload": {"event_id": "e1"}})
    assert len(store.coordinator_narratives) == 1
    assert "soc" in store.coordinator_narratives[0]
