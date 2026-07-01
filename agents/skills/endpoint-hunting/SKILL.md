---
name: endpoint-hunting
description: Proactive endpoint threat hunting for persistence and evasion
---

# Endpoint Threat Hunting

## When to use

- Hypothesis-driven hunts before SOC alert fires
- Persistence, fileless malware, LOLBin abuse
- Defense evasion and anomalous PowerShell execution

## Veil playbook anchors

- `hunting-for-registry-persistence-mechanisms`
- `detecting-fileless-malware-techniques`
- `hunting-for-anomalous-powershell-execution`
- `building-threat-hunt-hypothesis-framework`
- `hunting-for-scheduled-task-persistence`

## Output guidance

Set hunt_status explicitly. List detection_gaps when telemetry is insufficient. Map to technique_ids.
