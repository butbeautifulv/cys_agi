---
name: identity-attacks
description: AD/IAM credential access and lateral movement playbooks
---

# Identity & Access Attacks

## When to use

- Kerberoasting, DCSync, Pass-the-Ticket indicators
- AD ACL abuse and privilege escalation paths
- IAM anomaly correlation with endpoint alerts

## Veil playbook anchors

- `performing-kerberoasting-attack`
- `hunting-for-dcsync-attacks`
- `analyzing-active-directory-acl-abuse`
- `detecting-mimikatz-execution-patterns`
- `conducting-pass-the-ticket-attack`

## Output guidance

Populate lateral_movement_stage and mitre_techniques. Correlate identity_asset with evidence chain.
