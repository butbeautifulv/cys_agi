from __future__ import annotations

import json

import psycopg

from cys_core.domain.catalog.models import AgentCatalogEntry, CatalogSource, CatalogVersion, ProfilePack
from cys_core.infrastructure.catalog.hybrid_registry import ensure_catalog_schema


class PostgresAgentCatalog:
    def __init__(self, postgres_url: str) -> None:
        self._postgres_url = postgres_url
        with psycopg.connect(self._postgres_url) as conn:
            ensure_catalog_schema(conn)

    def _connect(self) -> psycopg.Connection:
        return psycopg.connect(self._postgres_url)

    def list_agents(self, *, profile_id: str | None = None, enabled_only: bool = True) -> list[AgentCatalogEntry]:
        clauses = ["1=1"]
        params: list[object] = []
        if profile_id:
            clauses.append("profile_id = %s")
            params.append(profile_id)
        if enabled_only:
            clauses.append("enabled = TRUE")
        sql = f"SELECT payload FROM agent_catalog WHERE {' AND '.join(clauses)} ORDER BY name"
        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [AgentCatalogEntry.model_validate(row[0]) for row in rows]

    def get_agent(self, name: str) -> AgentCatalogEntry | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload FROM agent_catalog WHERE name = %s ORDER BY version DESC LIMIT 1",
                (name,),
            ).fetchone()
        if row is None:
            return None
        return AgentCatalogEntry.model_validate(row[0])

    def upsert_agent(self, entry: AgentCatalogEntry) -> AgentCatalogEntry:
        existing = self.get_agent(entry.name)
        if existing is not None:
            entry.version = existing.version + 1
        entry.source = CatalogSource.API
        payload = entry.model_dump(mode="json")
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO agent_catalog (name, profile_id, payload, version, enabled, updated_at)
                VALUES (%s, %s, %s::jsonb, %s, %s, NOW())
                ON CONFLICT (name, profile_id) DO UPDATE SET
                    payload = EXCLUDED.payload,
                    version = EXCLUDED.version,
                    enabled = EXCLUDED.enabled,
                    updated_at = NOW()
                """,
                (entry.name, entry.profile_id, json.dumps(payload), entry.version, entry.enabled),
            )
            conn.commit()
        return entry

    def list_profiles(self) -> list[ProfilePack]:
        with self._connect() as conn:
            rows = conn.execute("SELECT payload FROM profile_packs ORDER BY id").fetchall()
        return [ProfilePack.model_validate(row[0]) for row in rows]

    def get_version(self, profile_id: str) -> CatalogVersion:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT COALESCE(MAX(version), 0), COUNT(*) FILTER (WHERE enabled)
                FROM agent_catalog WHERE profile_id = %s
                """,
                (profile_id,),
            ).fetchone()
        return CatalogVersion(profile_id=profile_id, version=int(row[0] or 0), agent_count=int(row[1] or 0))

    def seed(self, entries: list[AgentCatalogEntry], profile: ProfilePack) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO profile_packs (id, payload, updated_at)
                VALUES (%s, %s::jsonb, NOW())
                ON CONFLICT (id) DO UPDATE SET payload = EXCLUDED.payload, updated_at = NOW()
                """,
                (profile.id, json.dumps(profile.model_dump(mode="json"))),
            )
            for entry in entries:
                payload = entry.model_dump(mode="json")
                conn.execute(
                    """
                    INSERT INTO agent_catalog (name, profile_id, payload, version, enabled, updated_at)
                    VALUES (%s, %s, %s::jsonb, %s, %s, NOW())
                    ON CONFLICT (name, profile_id) DO UPDATE SET
                        payload = EXCLUDED.payload,
                        version = EXCLUDED.version,
                        enabled = EXCLUDED.enabled,
                        updated_at = NOW()
                    """,
                    (entry.name, entry.profile_id, json.dumps(payload), entry.version, entry.enabled),
                )
            conn.commit()
