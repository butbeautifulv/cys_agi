from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from typing import Any

from config import settings

from cys_core.infrastructure.kafka_topics import AUDIT_TOOL_INVOCATIONS_TOPIC
from tool_gateway.models import ToolInvokeRequest, ToolInvokeResponse

_audit_records: list[dict[str, Any]] = []


def get_audit_records() -> list[dict[str, Any]]:
    return list(_audit_records)


def clear_audit_records() -> None:
    _audit_records.clear()


def build_audit_record(request: ToolInvokeRequest, response: ToolInvokeResponse) -> dict[str, Any]:
    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "tool": request.tool_name,
        "persona": request.persona,
        "sandbox_id": request.sandbox_id,
        "job_id": request.job_id,
        "correlation_id": request.correlation_id,
        "success": response.success,
        "error": response.error,
        "args_keys": sorted(request.args.keys()),
    }


async def publish_audit_record(record: dict[str, Any]) -> bool:
    try:
        from aiokafka import AIOKafkaProducer

        producer = AIOKafkaProducer(bootstrap_servers=settings.kafka_bootstrap_servers)
        await producer.start()
        try:
            await producer.send_and_wait(
                AUDIT_TOOL_INVOCATIONS_TOPIC,
                json.dumps(record, ensure_ascii=False).encode(),
            )
            return True
        finally:
            await producer.stop()
    except Exception:
        return False


def publish_audit_record_sync(record: dict[str, Any]) -> bool:
    return asyncio.run(publish_audit_record(record))


def record_tool_invocation(request: ToolInvokeRequest, response: ToolInvokeResponse) -> None:
    record = build_audit_record(request, response)
    _audit_records.append(record)
    if settings.use_kafka:
        publish_audit_record_sync(record)
