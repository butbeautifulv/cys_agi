# External Skill Vetting

Product runtime skills live in `agents/skills/` (builtin, signed via content hash).

External packs must **never** land in the runtime path directly.

## Staging

- Drop third-party packs under `agents/skills/external/staging/`
- Staging is **not** loaded by `SkillRegistry` or workers

## Vetting checklist

1. SHA-256 hash recorded in registry manifest
2. Prompt injection scan (`source=skill`) on full `SKILL.md` body
3. Cisco Skill Scanner / manual review for `scripts/` auto-exec risk
4. Human L3 approval for `trust_tier: community`
5. Pin `version` + `hash` in `agents/manifest.yaml` — CI blocks drift

## Runtime rules

- Metadata only in agent context; body via `load_skill` → Skill Gateway
- Per-persona allowlist in `agent.yaml` `skills:`
- Audit topic: `audit.skill.loads`
