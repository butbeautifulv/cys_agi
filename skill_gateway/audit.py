from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from typing import Any

from config import settings

from cys_core.infrastructure.kafka_topics import AUDIT_SKILL_LOADS_TOPIC

_audit_records: list[dict[str, Any]] = []


def get_skill_audit_records() -> list[dict[str, Any]]:
    return list(_audit_records)


def clear_skill_audit_records() -> None:
    _audit_records.clear()


async def publish_skill_load(record: dict[str, Any]) -> bool:
    if not settings.use_kafka:
        return True
    try:
        from aiokafka import AIOKafkaProducer

        producer = AIOKafkaProducer(bootstrap_servers=settings.kafka_bootstrap_servers)
        await producer.start()
        try:
            await producer.send_and_wait(
                AUDIT_SKILL_LOADS_TOPIC,
                json.dumps(record, ensure_ascii=False).encode(),
            )
            return True
        finally:
            await producer.stop()
    except Exception:
        return False


def publish_skill_load_sync(record: dict[str, Any]) -> bool:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(publish_skill_load(record))
    return True


def record_skill_load(
    *,
    skill_name: str,
    persona: str,
    content_hash: str,
    job_id: str = "",
    trust_tier: str = "builtin",
) -> None:
    record = {
        "timestamp": datetime.now(UTC).isoformat(),
        "skill": skill_name,
        "persona": persona,
        "hash": content_hash,
        "job_id": job_id,
        "trust_tier": trust_tier,
    }
    _audit_records.append(record)
    if settings.use_kafka:
        publish_skill_load_sync(record)
