---
name: prompt-injection-defense
description: Detect and mitigate LLM prompt injection — direct, indirect, encoding, typoglycemia, jailbreak, RAG poisoning, and agent-specific attacks.
---

# prompt-injection-defense (cys-agi)

Extends: [cxado-skills/agent/prompt-injection-defense](../../../../shared/skills/agent/prompt-injection-defense/SKILL.md)

## cys-agi integration

| Layer | Location |
|-------|----------|
| Pattern filters | `cys_core/domain/security/patterns/` |
| Ingress sanitization | before LLM call |
| Global rules | `agents/rules/security.md` |
| Injection corpus (triage only) | `docs/injections/` — never copy payloads into code/tests |
| Tests | `tests/adversarial/` |

## Deep reference

- [reference.md](reference.md)
- [refs/owasp/LLM_Prompt_Injection_Prevention_Cheat_Sheet.md](../../../refs/owasp/LLM_Prompt_Injection_Prevention_Cheat_Sheet.md)
