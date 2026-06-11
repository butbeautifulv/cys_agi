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
| Redpanda (Kafka) | 9092 / 9644 / 8082 | none (dev-container) |

## Режимы работы

| STAGE | Persistence | Queue/Bus |
|-------|-------------|-----------|
| `test` | memory | in-memory fallback |
| `dev` | Postgres (fallback memory) | Redis or memory |
| `prod` | Postgres | Redis |

Локально без Docker:

```bash
USE_MEMORY_FALLBACK=true STAGE=dev python main.py ingest -t siem.alert -p '{"alert":"test"}'
USE_MEMORY_FALLBACK=true STAGE=dev python main.py worker --once
```

## Kafka / Redpanda (Phase 1)

Event bus для production-пути (Ingress → Kafka → router → worker daemon).
Локально поднимается через `docker compose` (single-node Redpanda, `dev-container`).

```bash
docker compose up -d redpanda

# Health и список топиков (rpk внутри контейнера)
docker compose exec redpanda rpk cluster health
docker compose exec redpanda rpk topic list

# Создать топики Phase 1 вручную (по желанию)
docker compose exec redpanda rpk topic create security.events.raw worker.jobs.soc bus.findings
```

| Переменная | Default | Назначение |
|------------|---------|------------|
| `USE_KAFKA` | `false` | Включает Kafka-путь (порты добавляются в P1.2.x) |
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:9092` | Адрес брокера (внутри compose — `redpanda:29092`) |

Пока `USE_KAFKA=false` — primary queue/bus остаётся Redis (`InMemory` fallback в `STAGE=test`).
Включение Kafka-портов (`KafkaJobQueue`, `KafkaBusTransport`) — подфазы P1.2.x.

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
