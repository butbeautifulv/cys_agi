from __future__ import annotations

import json
from typing import Any

import psycopg

from cys_core.application.ports.job_store import JobRecord
from cys_core.domain.workers.models import PendingHitlAction, WorkerJobStatus

_JOB_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS worker_jobs (
    job_id TEXT PRIMARY KEY,
    persona TEXT NOT NULL,
    event_id TEXT NOT NULL DEFAULT '',
    correlation_id TEXT NOT NULL DEFAULT '',
    tenant_id TEXT NOT NULL DEFAULT 'default',
    status TEXT NOT NULL,
    session_id TEXT NOT NULL DEFAULT '',
    payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    hitl_preview_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    pending_hitl_json JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_worker_jobs_status ON worker_jobs (status);
CREATE INDEX IF NOT EXISTS idx_worker_jobs_correlation ON worker_jobs (tenant_id, correlation_id);
"""


class PostgresJobStore:
    def __init__(self, postgres_url: str) -> None:
        self._postgres_url = postgres_url
        self._ensure_schema()

    def _connect(self) -> psycopg.Connection:
        return psycopg.connect(self._postgres_url)

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(_JOB_SCHEMA_SQL)
            conn.commit()

    def _upsert(
        self,
        *,
        job_id: str,
        session_id: str,
        persona: str,
        status: WorkerJobStatus,
        hitl_preview: dict[str, Any] | None = None,
        pending_hitl: PendingHitlAction | None = None,
    ) -> JobRecord:
        preview = hitl_preview or {}
        pending_json = pending_hitl.model_dump(mode="json") if pending_hitl else None
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO worker_jobs (
                    job_id, persona, status, session_id, hitl_preview_json, pending_hitl_json, updated_at
                ) VALUES (%s, %s, %s, %s, %s::jsonb, %s::jsonb, NOW())
                ON CONFLICT (job_id) DO UPDATE SET
                    persona = EXCLUDED.persona,
                    status = EXCLUDED.status,
                    session_id = EXCLUDED.session_id,
                    hitl_preview_json = EXCLUDED.hitl_preview_json,
                    pending_hitl_json = EXCLUDED.pending_hitl_json,
                    updated_at = NOW()
                """,
                (job_id, persona, status.value, session_id, json.dumps(preview), json.dumps(pending_json)),
            )
            conn.commit()
        return JobRecord(
            job_id=job_id,
            session_id=session_id,
            persona=persona,
            status=status,
            hitl_preview=preview,
            pending_hitl=pending_hitl,
        )

    def upsert_running(self, job_id: str, session_id: str, persona: str) -> JobRecord:
        return self._upsert(
            job_id=job_id,
            session_id=session_id,
            persona=persona,
            status=WorkerJobStatus.RUNNING,
        )

    def pause_for_hitl(self, pending: PendingHitlAction, preview: dict[str, Any]) -> JobRecord:
        return self._upsert(
            job_id=pending.job_id,
            session_id=pending.session_id,
            persona=pending.persona,
            status=WorkerJobStatus.AWAITING_APPROVAL,
            hitl_preview=preview,
            pending_hitl=pending,
        )

    def get(self, job_id: str) -> JobRecord | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT job_id, session_id, persona, status, hitl_preview_json, pending_hitl_json
                FROM worker_jobs WHERE job_id = %s
                """,
                (job_id,),
            ).fetchone()
        if row is None:
            return None
        pending = PendingHitlAction.model_validate(row[5]) if row[5] else None
        return JobRecord(
            job_id=row[0],
            session_id=row[1],
            persona=row[2],
            status=WorkerJobStatus(row[3]),
            hitl_preview=row[4] if isinstance(row[4], dict) else json.loads(row[4] or "{}"),
            pending_hitl=pending,
        )

    def mark_running(self, job_id: str) -> JobRecord | None:
        record = self.get(job_id)
        if record is None:
            return None
        return self._upsert(
            job_id=job_id,
            session_id=record.session_id,
            persona=record.persona,
            status=WorkerJobStatus.RUNNING,
            hitl_preview=record.hitl_preview,
            pending_hitl=None,
        )

    def mark_completed(self, job_id: str) -> None:
        record = self.get(job_id)
        if record is None:
            return
        self._upsert(
            job_id=job_id,
            session_id=record.session_id,
            persona=record.persona,
            status=WorkerJobStatus.COMPLETED,
            hitl_preview=record.hitl_preview,
        )

    def mark_failed(self, job_id: str) -> None:
        record = self.get(job_id)
        if record is None:
            return
        self._upsert(
            job_id=job_id,
            session_id=record.session_id,
            persona=record.persona,
            status=WorkerJobStatus.FAILED,
            hitl_preview=record.hitl_preview,
        )

    def list_pending_approvals(self) -> list[PendingHitlAction]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT pending_hitl_json FROM worker_jobs
                WHERE status = %s AND pending_hitl_json IS NOT NULL
                """,
                (WorkerJobStatus.AWAITING_APPROVAL.value,),
            ).fetchall()
        result: list[PendingHitlAction] = []
        for row in rows:
            if row[0]:
                result.append(PendingHitlAction.model_validate(row[0]))
        return result
