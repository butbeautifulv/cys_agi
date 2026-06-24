---
name: ai-agent-security
description: Secure AI agent architectures — tool least privilege, HITL, memory isolation, output guardrails, multi-agent trust, monitoring, and adversarial testing. Use when designing, reviewing, or hardening agent systems.
---

# ai-agent-security (cys-agi)

Extends: [cxado-skills/agent/ai-agent-security](../../../../shared/skills/agent/ai-agent-security/SKILL.md)

Read and apply the generic skill first; then apply cys-agi integration below.

## cys-agi integration

| Control | Location |
|---------|----------|
| Tool allowlist | `agent.yaml`; dangerous tools in `hitl_tools` |
| Input sanitization | ingress + `cys_core/domain/security/patterns/` |
| Multi-agent bus | `SecureAgentBus` — HMAC, trust levels, mTLS |
| HITL | `run_active_scan`, `write_file` when configured |
| Adversarial gate | `tests/adversarial/` in CI for security changes |
| Platform baseline | `agents/rules/security.md` |

## Deep reference

- [reference.md](reference.md)
- [refs/owasp/AI_Agent_Security_Cheat_Sheet.md](../../../refs/owasp/AI_Agent_Security_Cheat_Sheet.md)
