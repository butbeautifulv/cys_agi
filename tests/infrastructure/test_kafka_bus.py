from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from cys_core.infrastructure.kafka_bus import KafkaBusTransport


TEST_MSG = {"sender": "soc", "recipient": "critic", "type": "finding", "data": {"score": 0.9}}


def test_name():
    t = KafkaBusTransport()
    assert t.name == "kafka"


def test_requires_mtls():
    t = KafkaBusTransport()
    assert t.requires_mtls is False


def test_topic_naming():
    t = KafkaBusTransport()
    assert t._topic("findings") == "bus.findings"
    assert t._topic("critic") == "bus.critic"


def test_sync_send_delegates_to_fallback():
    t = KafkaBusTransport()
    result = t.send(TEST_MSG)
    assert result == TEST_MSG
    assert TEST_MSG in t._fallback.messages


def test_subscribe_registers_handler():
    t = KafkaBusTransport()
    handler = MagicMock()
    t.subscribe("critic", handler)
    assert handler in t._handlers["critic"]


@pytest.mark.asyncio
async def test_publish_dispatches_to_in_process_handler():
    t = KafkaBusTransport()
    received = []

    async def handler(msg):
        received.append(msg)

    t.subscribe("critic", handler)
    # Disable Kafka (not available in test env)
    t._available = False
    await t.publish("critic", TEST_MSG)
    assert received == [TEST_MSG]


@pytest.mark.asyncio
async def test_publish_kafka_failure_falls_back():
    """If Kafka producer raises, in-process dispatch still works."""
    t = KafkaBusTransport(bootstrap_servers="nonexistent:9999")
    t._available = True

    received = []

    async def handler(msg):
        received.append(msg)

    t.subscribe("findings", handler)

    mock_producer = AsyncMock()
    mock_producer.start = AsyncMock(side_effect=Exception("connection refused"))
    mock_producer.stop = AsyncMock()

    with patch("aiokafka.AIOKafkaProducer", return_value=mock_producer):
        await t.publish("findings", TEST_MSG)

    # In-process handler still fired
    assert received == [TEST_MSG]


def test_factory_returns_redis_when_use_kafka_false(monkeypatch):
    from config import Settings

    monkeypatch.setattr("cys_core.infrastructure.bus_transport.settings", Settings(_env_file=None))
    from cys_core.infrastructure.bus_transport import get_bus_transport

    get_bus_transport.cache_clear()
    t = get_bus_transport()
    assert t.name == "redis"
    get_bus_transport.cache_clear()


def test_factory_returns_kafka_when_use_kafka_true(monkeypatch):
    from config import Settings

    monkeypatch.setenv("USE_KAFKA", "true")
    s = Settings(_env_file=None)
    monkeypatch.setattr("cys_core.infrastructure.bus_transport.settings", s)
    from cys_core.infrastructure.bus_transport import get_bus_transport

    get_bus_transport.cache_clear()
    t = get_bus_transport()
    assert t.name == "kafka"
    get_bus_transport.cache_clear()
