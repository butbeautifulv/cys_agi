from __future__ import annotations

import json
from typing import Any

from cys_core.domain.rag.models import DocumentProvenance
from cys_core.domain.security.classification import DataClassification
from cys_core.infrastructure.kafka_topics import RAG_INGEST_STAGING_TOPIC
from rag.ingest.chunker import chunk_document
from rag.ingest.scanner import scan_document
from rag.store import get_vector_store


async def consume_staging_message(payload: dict[str, Any]) -> dict[str, Any]:
    """Process one staged ingest document."""
    text = str(payload.get("text", ""))
    scan = scan_document(text)
    if not scan.approved:
        return {"status": "rejected", "reason": scan.reason, "hash": scan.content_hash}

    provenance = DocumentProvenance(
        source_id=str(payload.get("source_id", "unknown")),
        source_name=str(payload.get("source_name", "")),
        uploaded_by=str(payload.get("uploaded_by", "")),
        content_hash=scan.content_hash,
        approved=True,
        metadata=dict(payload.get("metadata", {})),
    )
    chunks = chunk_document(
        text,
        provenance=provenance,
        tenant=str(payload.get("tenant", "default")),
        classification=DataClassification(payload.get("classification", DataClassification.INTERNAL)),
        roles=list(payload.get("roles", ["analyst"])),
    )
    count = get_vector_store().upsert(chunks)
    return {"status": "ingested", "chunks": count, "hash": scan.content_hash}


async def consume_staging_event(timeout: float = 1.0) -> dict[str, Any] | None:
    """Consume one message from rag.ingest.staging (Kafka or skip)."""
    try:
        from aiokafka import AIOKafkaConsumer

        from config import settings

        consumer = AIOKafkaConsumer(
            RAG_INGEST_STAGING_TOPIC,
            bootstrap_servers=settings.kafka_bootstrap_servers,
            group_id="rag-ingest",
            auto_offset_reset="earliest",
        )
        await consumer.start()
        try:
            import asyncio

            record = await asyncio.wait_for(consumer.getone(), timeout=timeout)
            payload = json.loads(record.value.decode())
            return await consume_staging_message(payload)
        finally:
            await consumer.stop()
    except Exception:
        return None
