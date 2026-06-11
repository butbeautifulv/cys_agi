# agents/ — продуктовый слой cys-agi

Runtime-конфигурация: personas, routing plans, rules, skills.

## Структура

```
agents/
├── manifest.yaml
├── personas/           # worker + control agents
├── rules/              # global constraints → system prompt
├── plans/              # event routing rules (event_types → personas)
└── skills/             # on-demand playbooks
```

## Как это загружается

| Папка | Загрузчик | Куда попадает |
|-------|-----------|---------------|
| `personas/` | `AgentRegistry` | Worker/control agent definitions |
| `rules/` | `ProductContext` | System prompt всех personas |
| `plans/` | `EventRouter.from_plans_dir()` | Event → persona dispatch |
| `skills/` | Deep Agents coordinator | On-demand domain knowledge |

## Personas

| Persona | Role | Фокус |
|---------|------|-------|
| redteam | worker | CI/CD, SAST, offensive analysis |
| network | worker | NetFlow, DNS, beaconing |
| soc | worker | SIEM alerts, triage, timeline |
| compliance | worker | Frameworks, evidence audit |
| critic | control | Finding validation, trust_score |
| coordinator | control | User status narratives |

## Plans (routing)

| Plan | Event types | Personas |
|------|-------------|----------|
| `incident-triage` | siem.alert, edr.alert, netflow.beacon | soc, network |
| `compliance-audit` | doc.upload, compliance.schedule | compliance |
| `redteam-engagement` | escalation (high+) | redteam |
| `full-assessment` | manual.investigation | all workers |

Default plan: `incident-triage` (см. `manifest.yaml`).

Подробнее: [plans/README.md](plans/README.md)

## Добавить persona

1. `personas/<name>/` — agent.yaml, AGENT.md, samples/
2. Routing rule в `plans/*.yaml`
3. Запись в `manifest.yaml`
4. `pytest tests/registry/`
