# Plans

Event routing playbooks — определяют **какой worker** запускается на **какой event**.

## Формат

```yaml
id: incident-triage
name: Incident triage
description: SOC and network workers for active incidents

routing:
  rules:
    - event_types: [siem.alert, edr.alert]
      min_severity: low
      personas: [soc]
      notify_control: true
    - event_types: [netflow.beacon]
      personas: [network]
```

## Планы

| Plan | Use case |
|------|----------|
| `incident-triage.yaml` | SIEM/EDR → soc; NetFlow → network (default) |
| `compliance-audit.yaml` | Documents, scheduled audits |
| `redteam-engagement.yaml` | High-severity escalations → redteam |
| `full-assessment.yaml` | Manual investigation → all workers |

Загрузка: `EventRouter.from_plans_dir(agents/plans/)`.

CLI `session -g "..."` отправляет `manual.investigation` event.
