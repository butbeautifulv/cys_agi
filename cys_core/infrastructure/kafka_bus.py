from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any

import structlog

from config import settings
from cys_core.infrastructure.bus_transport import BusHandler, InMemoryBusTransport

logger = structlog.get_logger(__name__)

TOPIC_PREFIX = "bus"


class KafkaBusTransport:
    """Kafka/Redpanda-backed bus transport for durable inter-agent messaging.

    Publish side: serializes messages to bus.{channel} topic.
    Subscribe side: stored handlers are invoked via in-memory dispatch (for same-process consumers).
    Cross-process consumers (critic/coordinator daemons) poll topics directly.
    """

    name = "kafka"
    requires_mtls = False

    def __init__(
        self,
        bootstrap_servers: str | None = None,
        consumer_group: str | None = None,
    ) -> None:
        self._bootstrap = bootstrap_servers or settings.kafka_bootstrap_servers
        self._group = consumer_group or f"{settings.kafka_consumer_group_prefix}-bus"
        self._handlers: dict[str, list[BusHandler]] = defaultdict(list)
        self._fallback = InMemoryBusTransport()
        self._available = False
        self._check_aiokafka()

    def _check_aiokafka(self) -> bool:
        try:
            import aiokafka  # noqa: F401

            self._available = True
            return True
        except ImportError:
            self._available = False
            return False

    def _topic(self, channel: str) -> str:
        return f"{TOPIC_PREFIX}.{channel}"

    def send(self, message: dict[str, Any]) -> dict[str, Any]:
        """Sync send — falls back to in-memory."""
        return self._fallback.send(message)

    async def send_async(self, message: dict[str, Any]) -> dict[str, Any]:
        return self.send(message)

    def subscribe(self, channel: str, handler: BusHandler) -> None:
        """Register in-process handler for a bus channel."""
        self._handlers[channel].append(handler)
        self._fallback.subscribe(channel, handler)

    async def publish(self, channel: str, message: dict[str, Any]) -> None:
        """Publish message to Kafka topic and dispatch to in-process handlers."""
        if self._available:
            try:
                from aiokafka import AIOKafkaProducer

                producer = AIOKafkaProducer(bootstrap_servers=self._bootstrap)
                await producer.start()
                try:
                    payload = json.dumps(message, ensure_ascii=False).encode()
                    await producer.send_and_wait(self._topic(channel), payload)
                    logger.debug("kafka_bus.published", channel=channel, topic=self._topic(channel))
                finally:
                    await producer.stop()
            except Exception as exc:
                logger.warning("kafka_bus.publish_failed", channel=channel, error=str(exc))

        # Always dispatch to in-process subscribers
        await self._fallback.publish(channel, message)
