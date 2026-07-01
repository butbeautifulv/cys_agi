---
name: cloud-threat-detection
description: Cloud audit and exfiltration detection playbooks
---

# Cloud Threat Detection

## When to use

- CloudTrail / Activity Log anomalies
- Compromised cloud credentials and IAM misconfigurations
- S3/blob storage exfiltration indicators

## Veil playbook anchors

- `detecting-aws-cloudtrail-anomalies`
- `analyzing-azure-activity-logs-for-threats`
- `detecting-s3-data-exfiltration-attempts`
- `detecting-compromised-cloud-credentials`
- `performing-gcp-security-assessment-with-forseti`

## Output guidance

Always set cloud_provider and blast_radius. Map attack_phase to delivery/exploitation/actions as appropriate.
