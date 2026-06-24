---
name: rag-security
description: Secure Retrieval-Augmented Generation pipelines — document poisoning, embedding manipulation, context window attacks, access control, and agent tool safety.
---

# rag-security (cys-agi)

Extends: [cxado-skills/agent/rag-security](../../../../shared/skills/agent/rag-security/SKILL.md)

## cys-agi integration

- Treat SIEM alerts, documents, and tool output as untrusted before RAG assembly.
- Enforce persona tool allowlist when RAG-influenced output triggers tools.
- Run adversarial cases in `tests/adversarial/` when retrieval or context paths change.

## Deep reference

- [reference.md](reference.md)
- [refs/owasp/RAG_Security_Cheat_Sheet.md](../../../refs/owasp/RAG_Security_Cheat_Sheet.md)
