# Product skills

Domain knowledge modules для on-demand загрузки (Deep Agents coordinator). Это **не** Cursor build-skills из `.agents/skills/`.

Каждая папка — `SKILL.md` с YAML frontmatter по [Agent Skills](https://github.com/anthropics/skills) формату.

| Skill | Когда использовать |
|-------|-------------------|
| `ai-agent-security` | Tool abuse, HITL, memory, multi-agent, adversarial testing |
| `prompt-injection-defense` | Direct/indirect injection, jailbreak, guardrails |
| `rag-security` | RAG pipeline: poisoning, ACL, vector store, agent+retrieval |
| `secure-deployment` | Zero trust, mTLS A2A, container hardening, prod config |
| `skill-supply-chain` | External skill/MCP vetting, Cisco AI Defense tooling |
| `ci-cd-threats` | GitHub Actions, supply chain, workflow risks |
| `network-beaconing` | NetFlow, DNS, C2 beaconing patterns |
| `compliance-frameworks` | SOC 2, ISO 27001, NIST CSF mapping |

Coordinator: `skills=["./agents/skills/"]` в runtime.
