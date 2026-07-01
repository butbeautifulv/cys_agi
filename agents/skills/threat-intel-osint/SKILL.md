---
name: threat-intel-osint
description: OSINT, MISP, and threat actor TTP analysis playbooks
---

# Threat Intelligence & OSINT

## When to use

- TI feed enrichment and IOC correlation
- OSINT on domains, certificates, and external attack surface
- Threat actor TTP profiling with MITRE ATT&CK mapping

## Veil playbook anchors

- `performing-open-source-intelligence-gathering`
- `collecting-threat-intelligence-with-misp`
- `analyzing-threat-actor-ttps-with-mitre-attack`
- `performing-dns-enumeration-and-zone-transfer`
- `analyzing-certificate-transparency-for-phishing`

## Output guidance

Populate mitre_techniques and attack_phase (typically recon). Cite source confidence for each IOC.
