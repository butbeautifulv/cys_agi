from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from cys_core.infrastructure.kafka_queue import KafkaJobQueue
from cys_core.domain.workers.models import RunResult
from workers.orchestrator import WorkerOrchestrator


TEST_JOB = {
    "job_id": "dlq-test-1",
    "event_id": "evt-1",
    "persona": "soc",
    "playbook_id": "",
    "payload": {},
    "correlation_id": "",
    "status": "pending",
    "sandbox_id": "",
    "feedback": "",
}


@pytest.mark.asyncio
async def test_send_to_dlq_no_kafka_fallback():
    """send_to_dlq logs a warning when aiokafka not available."""
    q = KafkaJobQueue()
    with patch.object(q, "_check_aiokafka", return_value=False):
        # Should not raise
        await q.send_to_dlq(TEST_JOB, error="test error")


@pytest.mark.asyncio
async def test_send_to_dlq_kafka_publishes():
    """send_to_dlq publishes to DLQ topic via AIOKafkaProducer."""
    q = KafkaJobQueue(bootstrap_servers="localhost:9092")

    mock_producer = AsyncMock()
    mock_producer.start = AsyncMock()
    mock_producer.stop = AsyncMock()
    mock_producer.send_and_wait = AsyncMock()

    with patch.object(q, "_check_aiokafka", return_value=True):
        with patch("aiokafka.AIOKafkaProducer", return_value=mock_producer):
            await q.send_to_dlq(TEST_JOB, error="job crashed")

    mock_producer.send_and_wait.assert_called_once()
    topic = mock_producer.send_and_wait.call_args[0][0]
    assert topic == "worker.jobs.dlq"


@pytest.mark.asyncio
async def test_process_next_routes_failed_job_to_dlq():
    """WorkerOrchestrator routes failed jobs to DLQ when queue supports it."""
    mock_queue = AsyncMock()
    mock_queue.adequeue = AsyncMock(return_value=TEST_JOB)
    mock_queue.send_to_dlq = AsyncMock()

    mock_result = RunResult(
        job_id="dlq-test-1", persona="soc", success=False, error="worker crashed"
    )

    orch = MagicMock(spec=WorkerOrchestrator)
    orch.queue = mock_queue
    orch.run_job = AsyncMock(return_value=mock_result)
    orch.process_next = WorkerOrchestrator.process_next.__get__(orch)

    result = await orch.process_next()

    assert result is not None
    assert not result.success
    mock_queue.send_to_dlq.assert_called_once_with(TEST_JOB, error="worker crashed")


@pytest.mark.asyncio
async def test_process_next_no_dlq_on_success():
    """Successful jobs are NOT routed to DLQ."""
    mock_queue = AsyncMock()
    mock_queue.adequeue = AsyncMock(return_value=TEST_JOB)
    mock_queue.send_to_dlq = AsyncMock()

    mock_result = RunResult(job_id="dlq-test-1", persona="soc", success=True)

    orch = MagicMock(spec=WorkerOrchestrator)
    orch.queue = mock_queue
    orch.run_job = AsyncMock(return_value=mock_result)
    orch.process_next = WorkerOrchestrator.process_next.__get__(orch)

    await orch.process_next()

    mock_queue.send_to_dlq.assert_not_called()


@pytest.mark.asyncio
async def test_dlq_topic_name():
    assert KafkaJobQueue.DLQ_TOPIC == "worker.jobs.dlq"
