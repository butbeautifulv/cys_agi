# Архитектура cys-agi

## Обзор

cys-agi — **event-driven** multi-agent SOC platform с тремя плоскостями:

1. **Ingress** (`ingress/`) — приём structured events (CLI, FastAPI, webhooks)
2. **Control plane** (`control/`, `cys_core/domain/events/`) — router, critic, coordinator
3. **Worker plane** (`workers/`, ephemeral sandbox) — автономные domain agents per event

Единый **AgentRuntime** + **AgentRegistry** для LLM worker runs. Batch LangGraph pipeline (`graph/workflow.py`) **deprecated** — заменён event ingress.

## Data flow: event-driven

```
SIEM / NetFlow / Doc / Manual
         │
         ▼
   EventIngress.ingest()
         │
         ▼
   EventRouter (agents/plans/*.yaml routing rules)
         │
         ▼
   Redis JobQueue.enqueue(WorkerJob)
         │
         ▼
   WorkerOrchestrator.process_next()
         │
         ├── SandboxConnector.create(run_id, persona)
         ├── AgentRuntime.arun(persona, event_payload)
         ├── OutputGuardrails.validate_schema()
         ├── SecureAgentBus.send_message(finding)
         ├── BusTransport.publish(critic, coordinator)
         └── SandboxConnector.destroy(run_id)
         │
         ▼
   CriticService.handle_message()  — trust_score, feedback
   CoordinatorService.handle_message()  — user narrative
```

## Роли агентов

### Workers (ephemeral)

| Persona | Event types | Bus recipients |
|---------|-------------|----------------|
| soc | `siem.alert`, `edr.alert`, `iam.event` | network, critic, coordinator |
| network | `netflow.beacon`, `dns.anomaly`, `escalation` | soc, critic |
| redteam | `escalation`, `manual.investigation` (high+) | critic, coordinator |
| compliance | `doc.upload`, `compliance.schedule` | critic, coordinator |

### Control (always on)

| Persona | Роль |
|---------|------|
| critic | Observer: валидация findings, trust_score, async feedback |
| coordinator | Control tower: narratives для user, bus subscriber |

## Decision layers

1. **EventRouter** — deterministic rules from `agents/plans/`
2. **ScopePolicy + RiskLevel** — per-agent tool allowlist, HITL gates
3. **AgentRuntime** — LLM execution in sandbox with middleware
4. **OutputGuardrails** — schema validation, PII, exfiltration
5. **CriticService** — post-hoc quality gate (не блокирует worker inline)

## Ports (`cys_core/application/ports.py`)

| Port | Реализация |
|------|------------|
| `PersistenceConnector` | `cys_core/persistence.py` |
| `ModelConnector` | `cys_core/llm/` |
| `SandboxConnector` | `cys_core/infrastructure/sandbox.py` |
| `JobQueueConnector` | `cys_core/infrastructure/queue.py` |
| `AgentTransportConnector` | `cys_core/infrastructure/bus_transport.py` |

## Domain layer (`cys_core/domain/`)

| Bounded context | Содержание |
|-----------------|------------|
| `domain/events` | `SecurityEvent`, `EventRouter`, plan routing |
| `domain/workers` | `WorkerJob`, `RunResult`, `SandboxCredentials` |
| `domain/agents` | `AgentConfig`, `build_interrupt_on` |
| `domain/findings` | Finding schemas, `CriticResult` |
| `domain/security` | Sanitizer, guardrails, scope, agent bus |
| `domain/assessment` | Legacy HitlPolicy, report builder |

## Plans = routing rules

`agents/plans/*.yaml` содержат `routing.rules`:

```yaml
routing:
  rules:
    - event_types: [siem.alert, edr.alert]
      personas: [soc]
      notify_control: true
```

| Plan | Назначение |
|------|------------|
| `incident-triage` | SOC + network (default) |
| `compliance-audit` | Compliance worker |
| `redteam-engagement` | Redteam on escalation |
| `full-assessment` | Manual investigation — all workers |

## API (`ingress/api.py`)

| Endpoint | Описание |
|----------|----------|
| `POST /events` | Ingest structured event |
| `GET /status` | Control plane snapshot |
| `POST /workers/process-one` | Process next queued job |

## Security

- **SecureAgentBus**: A2A `a2a/1.0`, HMAC, replay window, trust levels
- **Middleware**: PromptContext, Scope, Security (rate limit, risk gate)
- **MCP tools**: `cys_core/registry/mcp_tools.py` — sandbox-scoped invocation
- **Sandbox**: `LocalSandboxConnector` (MVP); prod → K8s Job / E2B

## Deprecated

- `graph/workflow.py` `run_assessment` → redirects to `EventIngress`
- `graph/nodes.py` batch pipeline nodes — legacy, не используется в event flow

## Зависимости

| Пакет | Роль |
|-------|------|
| `langchain` | `create_agent`, middleware |
| `langgraph` | Checkpointer (optional sessions) |
| `deepagents` | Coordinator sessions (optional) |
| `litellm` | LLM provider |
| `fastapi` + `uvicorn` | Event/status API |
| `redis` | Job queue + bus transport |
