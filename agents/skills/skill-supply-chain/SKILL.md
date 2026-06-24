---
name: skill-supply-chain
description: Vet external agent skills and MCP servers for prompt injection, hidden instructions, and auto-exec risk.
---

# skill-supply-chain (cys-agi)

Extends: [cxado-skills/agent/skill-supply-chain](../../../../shared/skills/agent/skill-supply-chain/SKILL.md)

## cys-agi skill lifecycle

| Stage | Location | Runtime? |
|-------|----------|----------|
| Builtin (signed) | `agents/skills/` | Yes — SkillRegistry |
| External staging | `agents/skills/external/staging/` | **No** |
| Vetted external | pinned in `agents/manifest.yaml` | Yes — after L3 approval |

### Runtime rules

- Metadata only in context; body via `load_skill` → Skill Gateway
- Per-persona allowlist in `agent.yaml` `skills:`
- Audit topic: `audit.skill.loads`

## Deep reference

- [reference.md](reference.md)
- `docs/SKILLS_VETTING.md`
- [docs/reference/CISCO_AI_DEFENCE.md](../../../docs/reference/CISCO_AI_DEFENCE.md)
