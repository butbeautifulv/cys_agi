# Разработка cys-agi

## Окружение

```bash
uv sync --group dev
docker compose up -d
cp .env.example .env
```

| Service | Port | Credentials |
|---------|------|-------------|
| Postgres 16 | 5432 | `postgres` / `password`, DB `cys_agi` |
| Redis 7 | 6379 | password `password` |
| Redpanda | 9092 | no auth (dev) |
| Redpanda Schema Registry | 8081 | — |
| Redpanda HTTP Proxy | 8082 | — |

## Режимы работы

| STAGE | Persistence | Queue/Bus |
|-------|-------------|-----------|
| `test` | memory | in-memory fallback |
| `dev` | Postgres (fallback memory) | Redis or memory |
| `dev` + `USE_KAFKA=true` | Postgres | Redpanda/Kafka |
| `prod` | Postgres | Redpanda/Kafka |

Локально без Docker:

```bash
USE_MEMORY_FALLBACK=true STAGE=dev python main.py ingest -t siem.alert -p '{"alert":"test"}'
USE_MEMORY_FALLBACK=true STAGE=dev python main.py worker --once
```

## Kafka / Redpanda (Phase 1+)

Redpanda — Kafka-совместимый брокер, используется для event bus в prod.

### Запуск с Kafka

```bash
# Запустить все сервисы включая Redpanda
docker compose up -d

# Проверить состояние кластера
docker compose exec redpanda rpk cluster health

# Список топиков
docker compose exec redpanda rpk topic list

# Запустить с Kafka включённым
USE_KAFKA=true python main.py ingest -t siem.alert -p '{"alert":"test"}'
USE_KAFKA=true python main.py worker --once
```

### Kafka topics

| Topic | Producer | Consumer | Retention |
|-------|----------|----------|-----------|
| `security.events.raw` | Ingress API | router-consumer | 7d |
| `worker.jobs.{persona}` | router | worker-{persona} daemon | 3d |
| `bus.findings` | workers | critic, coordinator | 30d |
| `security.events.escalation` | critic, workers | router | 7d |
| `worker.jobs.dlq` | workers | DLQ consumer | 7d |

### Feature flag

`USE_KAFKA=false` (default) → Redis queue + in-memory bus (backward compatible).
`USE_KAFKA=true` → KafkaJobQueue + KafkaBusTransport.

## CLI для отладки

```bash
python main.py info

# Event-driven flow
python main.py ingest -t siem.alert -p '{"alert":"powershell"}' -s high
python main.py worker --once
python main.py status

# API
python main.py serve --port 8080
curl -X POST http://localhost:8080/events \
  -H 'Content-Type: application/json' \
  -d '{"event_type":"siem.alert","payload":{"alert":"test"}}'

# Manual investigation (all workers)
python main.py session -g "Analyze workflow risks"

# Single worker debug
python main.py agent soc
python main.py agent redteam -i "sample input"
```

## Тестирование

```bash
USE_MEMORY_FALLBACK=true STAGE=test uv run pytest tests/ -q --cov=cys_core/domain

uv run pytest tests/domain/events/ -v
uv run pytest tests/workers/ -v
uv run pytest tests/ingress/ -v
uv run pytest tests/control/ -v
uv run pytest tests/adversarial/ -v
```

## Добавление persona

### agent.yaml

```yaml
name: myagent
description: Short description
role: worker              # worker | control
output_schema: MyFinding
tools:
  - dedup_alerts
hitl_tools: {}
trust_level: internal
bus_recipients:
  - critic
  - coordinator
language: ru
sample: samples/default.txt
```

### Routing rule

Добавить в `agents/plans/<plan>.yaml`:

```yaml
routing:
  rules:
    - event_types: [my.event.type]
      personas: [myagent]
      notify_control: true
```

### manifest.yaml

Добавить в `personas.workers` или `personas.control`.

## Добавление event type

1. Добавить literal в `cys_core/domain/events/models.py` → `EventType`
2. Routing rule в plan YAML
3. Тест в `tests/domain/events/`

## Структура event-driven кода

```
ingress/router.py       # EventIngress
workers/orchestrator.py # WorkerOrchestrator
control/                # CriticService, CoordinatorService, StatusStore
cys_core/domain/events/ # SecurityEvent, EventRouter
cys_core/infrastructure/# sandbox, queue, bus_transport
```

## Langfuse (опционально)

```bash
LANGFUSE_API_KEY=...
LANGFUSE_HOST=https://cloud.langfuse.com
```
