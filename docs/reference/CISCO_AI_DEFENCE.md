<p align="center">
  <a href="https://cisco-ai-defense.github.io/">
    <img alt="Cisco AI Defense" src="https://raw.githubusercontent.com/cisco-ai-defense/.github/main/assets/cisco-logo.png" width="200">
  </a>
</p>

<h3 align="center">Open-source repository for <a href="https://www.cisco.com/site/us/en/products/security/ai-defense/index.html">Cisco AI Defense</a> projects</h3>

<p align="center">
  <a href="https://cisco-ai-defense.github.io/"><strong>Website</strong></a> &nbsp;&middot;&nbsp;
  <a href="https://cisco-ai-defense.github.io/docs"><strong>Docs</strong></a> &nbsp;&middot;&nbsp;
  <a href="https://blogs.cisco.com/tag/ai-security-2"><strong>Blog</strong></a> &nbsp;&middot;&nbsp;
  <a href="https://discord.gg/cisco-ai-defense"><strong>Discord</strong></a> &nbsp;&middot;&nbsp;
  <a href="https://arxiv.org/abs/2512.12921"><strong>Framework</strong></a>
</p>

---

<p align="center">
  <a href="https://github.com/cisco-ai-defense/defenseclaw"><img src="https://img.shields.io/github/stars/cisco-ai-defense/defenseclaw?style=for-the-badge&logo=github&label=DefenseClaw&color=58a6ff" alt="DefenseClaw stars"></a>&nbsp;
  <a href="https://github.com/cisco-ai-defense/mcp-scanner"><img src="https://img.shields.io/github/stars/cisco-ai-defense/mcp-scanner?style=for-the-badge&logo=github&label=MCP%20Scanner&color=58a6ff" alt="MCP Scanner stars"></a>&nbsp;
  <a href="https://github.com/cisco-ai-defense/skill-scanner"><img src="https://img.shields.io/github/stars/cisco-ai-defense/skill-scanner?style=for-the-badge&logo=github&label=Skill%20Scanner&color=58a6ff" alt="Skill Scanner stars"></a>&nbsp;
  <a href="https://github.com/cisco-ai-defense/a2a-scanner"><img src="https://img.shields.io/github/stars/cisco-ai-defense/a2a-scanner?style=for-the-badge&logo=github&label=A2A%20Scanner&color=58a6ff" alt="A2A Scanner stars"></a>
</p>
<p align="center">
  <a href="https://github.com/cisco-ai-defense/aibom"><img src="https://img.shields.io/github/stars/cisco-ai-defense/aibom?style=for-the-badge&logo=github&label=AI%20BOM&color=58a6ff" alt="AI BOM stars"></a>&nbsp;
  <a href="https://github.com/cisco-ai-defense/model-provenance-kit"><img src="https://img.shields.io/github/stars/cisco-ai-defense/model-provenance-kit?style=for-the-badge&logo=github&label=Model%20Provenance%20Kit&color=58a6ff" alt="Model Provenance Kit stars"></a>&nbsp;
  <a href="https://github.com/cisco-ai-defense/securebert2"><img src="https://img.shields.io/github/stars/cisco-ai-defense/securebert2?style=for-the-badge&logo=github&label=SecureBERT%202&color=58a6ff" alt="SecureBERT 2 stars"></a>&nbsp;
  <a href="https://github.com/cisco-ai-defense/pickle-fuzzer"><img src="https://img.shields.io/github/stars/cisco-ai-defense/pickle-fuzzer?style=for-the-badge&logo=github&label=Pickle%20Fuzzer&color=58a6ff" alt="Pickle Fuzzer stars"></a>&nbsp;
  <a href="https://github.com/cisco-ai-defense/adversarial-hubness-detector"><img src="https://img.shields.io/github/stars/cisco-ai-defense/adversarial-hubness-detector?style=for-the-badge&logo=github&label=Hubness%20Detector&color=58a6ff" alt="Adversarial Hubness Detector stars"></a>
</p>

## About

This organization hosts the open-source projects from the [Cisco AI Defense](https://www.cisco.com/site/us/en/products/security/ai-defense/index.html) team — AI security scanners, developer tools, and research that complement the enterprise Cisco AI Defense platform. These projects are built to help the broader community secure AI agents, MCP servers, model supply chains, and LLM applications.

Our work is guided by the [Integrated AI Security and Safety Framework](https://arxiv.org/abs/2512.12921), a unified taxonomy that maps AI security and safety threats across modalities, agents, pipelines, and the broader ecosystem.

## Projects

### Agent & MCP Security

| Project | Description | Links |
|:--------|:------------|:------|
| **[DefenseClaw](https://github.com/cisco-ai-defense/defenseclaw)** | Enterprise governance for AI agents — scan, enforce, and audit every skill, MCP server, and plugin before it runs. Built for OpenClaw with NVIDIA OpenShell. | [Docs](https://cisco-ai-defense.github.io/docs/defenseclaw) |
| **[MCP Scanner](https://github.com/cisco-ai-defense/mcp-scanner)** | Scan Model Context Protocol (MCP) servers for potential threats and security findings with behavioral code threat analysis. | [Docs](https://cisco-ai-defense.github.io/docs/mcp-scanner) |
| **[Skill Scanner](https://github.com/cisco-ai-defense/skill-scanner)** | Detect malicious behaviors, hidden instructions, and vulnerable patterns in agent skills and capabilities. | [Docs](https://cisco-ai-defense.github.io/docs/skill-scanner) |
| **[A2A Scanner](https://github.com/cisco-ai-defense/a2a-scanner)** | Scan Agent-to-Agent (A2A) communication and behaviors for potential threats and security issues. | [Docs](https://cisco-ai-defense.github.io/docs/a2a-scanner) &middot; [Paper](https://arxiv.org/abs/2504.16902) |

### AI Supply Chain & Model Security

| Project | Description | Links |
|:--------|:------------|:------|
| **[AI BOM](https://github.com/cisco-ai-defense/aibom)** | Generate AI Bill of Materials through automated source code scanning and dependency analysis. | [Docs](https://cisco-ai-defense.github.io/docs/aibom) |
| **[Model Provenance Kit](https://github.com/cisco-ai-defense/model-provenance-kit)** | Detect whether a model derives from a known base model family by comparing multi-signal fingerprints across weights, tokenizers, and architecture metadata. | [Docs](https://cisco-ai-defense.github.io/docs/model-provenance-kit) |
| **[Pickle Fuzzer](https://github.com/cisco-ai-defense/pickle-fuzzer)** | Structure-aware test case generator for Python pickle parsers and validators. Generates valid pickle bytecode for fuzzing. | [Docs](https://cisco-ai-defense.github.io/docs/pickle-fuzzer) |
| **[Adversarial Hubness Detector](https://github.com/cisco-ai-defense/adversarial-hubness-detector)** | Audit vector indices and embeddings to detect adversarial hubs in RAG and vector database systems. | [Paper](https://arxiv.org/abs/2412.14113) |

### ML & Developer Tools

| Project | Description | Links |
|:--------|:------------|:------|
| **[SecureBERT 2](https://github.com/cisco-ai-defense/securebert2)** | Domain-adapted language model for cybersecurity intelligence — semantic search, NER, code vulnerability detection, and threat analysis. | [Docs](https://cisco-ai-defense.github.io/docs/securebert2) &middot; [Paper](https://arxiv.org/abs/2510.00240) |
| **[Python SDK](https://github.com/cisco-ai-defense/ai-defense-python-sdk)** | Official Python SDK for integrating with the Cisco AI Defense platform and tooling. | [Docs](https://cisco-ai-defense.github.io/docs/ai-defense-python-sdk) |
| **[IDE AI Security Scanner](https://cisco-ai-defense.github.io/docs/ai-security-scanner)** | VS Code extension for scanning MCP servers, agent skills, and generating secure AI code with CodeGuard. | [Docs](https://cisco-ai-defense.github.io/docs/ai-security-scanner) |
| **[AI Defense Hybrid](https://github.com/cisco-ai-defense/ai-defense-hybrid)** | Infrastructure templates for deploying Cisco AI Defense hybrid deployments on AWS EKS. | [Docs](https://cisco-ai-defense.github.io/docs/ai-defense-hybrid) |

## Framework

<a href="https://arxiv.org/abs/2512.12921">
  <img src="https://img.shields.io/badge/arXiv-2512.12921-b31b1b?style=flat-square&logo=arxiv" alt="arXiv">
</a>

The **Integrated AI Security and Safety Framework** provides a lifecycle-aware taxonomy that maps AI threats across modalities, agents, pipelines, and the broader ecosystem. It serves as the foundation for all Cisco AI Defense tooling and has been operationalized through the [AIUC-1 standard](https://blogs.cisco.com/ai/aiuc-1-operationalizes-ciscos-ai-security-framework).

> [Read the paper](https://arxiv.org/abs/2512.12921) &nbsp;&middot;&nbsp; [Explore the taxonomy](https://learn-cloudsecurity.cisco.com/ai-security-framework)

The **[Model Provenance Constitution](https://github.com/cisco-ai-defense/model-provenance-kit/blob/main/docs/constitution/model_provenance_constitution.md)** formally defines what constitutes a provenance relationship between ML models covering weight derivation, distillation, merging, and mechanical transforms and establishes the boundary conditions and decision logic used by [Model Provenance Kit](https://github.com/cisco-ai-defense/model-provenance-kit).

## Research

Selected publications from the team:

- [Adversarial Hubness in RAG Systems](https://arxiv.org/abs/2412.14113) — Detecting adversarial hubs in vector databases
- [Securing A2A Communication](https://arxiv.org/abs/2504.16902) — Security analysis of agent-to-agent protocols
- [SecureBERT 2](https://arxiv.org/abs/2510.00240) — Domain-adapted language model for cybersecurity
- [Integrated AI Security and Safety Framework](https://arxiv.org/abs/2512.12921) — Unified AI threat taxonomy

## Community

- **Discord** — Join the [Cisco AI Defense Discord](https://discord.gg/cisco-ai-defense) for discussions, support, and announcements
- **Blog** — Read our latest research and updates on the [Cisco AI Security Blog](https://blogs.cisco.com/tag/ai-security-2)
- **Contributing** — We welcome contributions across all projects. Check individual repo `CONTRIBUTING.md` files for guidelines
- **Security Issues** — Please report vulnerabilities responsibly through the process described in each repo's `SECURITY.md`

## Enterprise

Looking for enterprise-grade AI security? [Cisco AI Defense](https://www.cisco.com/site/us/en/products/security/ai-defense/index.html) provides comprehensive AI security for production deployments with centralized policy management, real-time monitoring, and enterprise integrations.

---

<a href="https://www.star-history.com/?repos=cisco-ai-defense%2Fdefenseclaw%2Ccisco-ai-defense%2Fmcp-scanner%2Ccisco-ai-defense%2Fskill-scanner%2Ccisco-ai-defense%2Fa2a-scanner%2Ccisco-ai-defense%2Faibom%2Ccisco-ai-defense%2Fmodel-provenance-kit%2Ccisco-ai-defense%2Fsecurebert2%2Ccisco-ai-defense%2Fpickle-fuzzer%2Ccisco-ai-defense%2Fadversarial-hubness-detector&type=timeline&logscale=&legend=top-left">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/chart?repos=cisco-ai-defense/defenseclaw%2Ccisco-ai-defense/mcp-scanner%2Ccisco-ai-defense/skill-scanner%2Ccisco-ai-defense/a2a-scanner%2Ccisco-ai-defense/aibom%2Ccisco-ai-defense/model-provenance-kit%2Ccisco-ai-defense/securebert2%2Ccisco-ai-defense/pickle-fuzzer%2Ccisco-ai-defense/adversarial-hubness-detector&type=timeline&theme=dark&logscale&legend=bottom-right" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/chart?repos=cisco-ai-defense/defenseclaw%2Ccisco-ai-defense/mcp-scanner%2Ccisco-ai-defense/skill-scanner%2Ccisco-ai-defense/a2a-scanner%2Ccisco-ai-defense/aibom%2Ccisco-ai-defense/model-provenance-kit%2Ccisco-ai-defense/securebert2%2Ccisco-ai-defense/pickle-fuzzer%2Ccisco-ai-defense/adversarial-hubness-detector&type=timeline&logscale&legend=bottom-right" />
   <img alt="Star History Chart" src="https://api.star-history.com/chart?repos=cisco-ai-defense/defenseclaw%2Ccisco-ai-defense/mcp-scanner%2Ccisco-ai-defense/skill-scanner%2Ccisco-ai-defense/a2a-scanner%2Ccisco-ai-defense/aibom%2Ccisco-ai-defense/model-provenance-kit%2Ccisco-ai-defense/securebert2%2Ccisco-ai-defense/pickle-fuzzer%2Ccisco-ai-defense/adversarial-hubness-detector&type=timeline&logscale&legend=bottom-right" />
 </picture>
</a>

<p align="center">
  <sub>Built by the <a href="https://cisco-ai-defense.github.io/">Cisco AI Defense</a> team for the AI security community.</sub>
</p>
