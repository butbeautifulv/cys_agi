from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Awaitable, Callable
from functools import lru_cache
from typing import Any

from config import settings

BusHandler = Callable[[dict[str, Any]], Awaitable[None] | None]


class InMemoryBusTransport:
    """In-process bus transport for tests and single-node dev."""

    name = "memory"
    requires_mtls = False

    def __init__(self) -> None:
        self._handlers: dict[str, list[BusHandler]] = defaultdict(list)
        self._messages: list[dict[str, Any]] = []

    def send(self, message: dict[str, Any]) -> dict[str, Any]:
        self._messages.append(message)
        return message

    async def send_async(self, message: dict[str, Any]) -> dict[str, Any]:
        return self.send(message)

    def subscribe(self, channel: str, handler: BusHandler) -> None:
        self._handlers[channel].append(handler)

    async def publish(self, channel: str, message: dict[str, Any]) -> None:
        for handler in self._handlers.get(channel, []):
            result = handler(message)
            if hasattr(result, "__await__"):
                await result

    @property
    def messages(self) -> list[dict[str, Any]]:
        return list(self._messages)


class RedisBusTransport:
    """Redis pub/sub bus transport between worker pods."""

    name = "redis"
    requires_mtls = True
    CHANNEL_PREFIX = "cys:bus:"

    def __init__(self, redis_url: str | None = None) -> None:
        self._fallback = InMemoryBusTransport()
        self._handlers: dict[str, list[BusHandler]] = defaultdict(list)
        self._redis = None
        self._redis_url = redis_url or settings.redis_url
        try:
            import redis

            self._redis = redis.Redis.from_url(self._redis_url, decode_responses=True)
            self._redis.ping()
        except Exception:
            self._redis = None

    def _channel(self, name: str) -> str:
        return f"{self.CHANNEL_PREFIX}{name}"

    def send(self, message: dict[str, Any]) -> dict[str, Any]:
        if self._redis is None:
            return self._fallback.send(message)
        recipient = message.get("recipient", "broadcast")
        self._redis.publish(self._channel(recipient), json.dumps(message, ensure_ascii=False))
        return message

    async def send_async(self, message: dict[str, Any]) -> dict[str, Any]:
        return self.send(message)

    def subscribe(self, channel: str, handler: BusHandler) -> None:
        self._handlers[channel].append(handler)
        if self._redis is not None:
            self._fallback.subscribe(channel, handler)

    async def publish(self, channel: str, message: dict[str, Any]) -> None:
        if self._redis is not None:
            self._redis.publish(self._channel(channel), json.dumps(message, ensure_ascii=False))
        await self._fallback.publish(channel, message)


@lru_cache
def get_bus_transport() -> RedisBusTransport:
    if settings.use_kafka:
        from cys_core.infrastructure.kafka_bus import KafkaBusTransport

        return KafkaBusTransport()  # type: ignore[return-value]
    return RedisBusTransport()
