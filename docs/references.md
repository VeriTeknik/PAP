# PAP References and Bibliography

**Protocol Version**: PAP v1.0 (Paper-Aligned)
**Paper Version**: Draft v0.3 (for arXiv cs.DC)
**Last Updated**: November 12, 2025

This document consolidates all academic and technical references used throughout the PAP documentation. References are organized by category for easy navigation.

---

## Table of Contents

- [Primary Academic Paper](#primary-academic-paper)
- [Protocol Specifications](#protocol-specifications)
- [Standards and RFCs](#standards-and-rfcs)
- [Agent Systems Research](#agent-systems-research)
- [Multi-Agent Coordination](#multi-agent-coordination)
- [Security and Trust](#security-and-trust)
- [Governance and Compliance](#governance-and-compliance)
- [Protocol Interoperability](#protocol-interoperability)
- [BibTeX Entries](#bibtex-entries)

---

## Primary Academic Paper

**[0] The Plugged.in Agent Protocol (PAP)**

```
C. Karaca, "The Plugged.in Agent Protocol (PAP): A Comprehensive Framework
for Autonomous Agent Lifecycle Management," Draft v0.3 for arXiv cs.DC,
VeriTeknik & Plugged.in, November 2025.
```

**Keywords**: autonomous agents, control plane, lifecycle management, mTLS, OAuth 2.1, JSON-RPC, gRPC, Ed25519, audit, DNS, ownership transfer, heartbeat, telemetry, MCP, A2A, interoperability

**Abstract**: PAP establishes a dual-profile framework (PAP-CP for control plane operations, PAP-Hooks for open ecosystem integration) addressing critical gaps in autonomous agent reliability through strict heartbeat/telemetry separation, normative lifecycle states, and comprehensive security.

**Repository**: https://github.com/VeriTeknik/PAP

---

## Protocol Specifications

### [1] Model Context Protocol (MCP)

**Author**: Anthropic
**Version**: 2025-06-18
**URL**: https://modelcontextprotocol.io/specification/2025-06-18/

**Summary**: JSON-RPC 2.0 protocol for LLM tool integration with three primitives: Resources, Tools, and Prompts. PAP adopts MCP patterns for PAP-Hooks while adding lifecycle management.

**PAP Integration**: PAP-Hooks profile uses MCP-compatible JSON-RPC 2.0 format for tool invocations.

### [2] Agent-to-Agent Protocol (A2A)

**Author**: Linux Foundation
**Version**: v0.3.0
**URL**: https://a2a-protocol.org/latest/specification/

**Summary**: Stateless peer delegation protocol through Agent Cards. PAP complements A2A by adding stateful orchestration, shared memory, and centralized governance.

**PAP Integration**: PAP-Hooks enables A2A delegation via `a2a.delegate` method; Service Registry publishes Agent Cards.

### [3] JSON-RPC 2.0

**Author**: JSON-RPC Working Group
**Version**: 2.0
**URL**: https://www.jsonrpc.org/specification

**Summary**: Stateless, light-weight remote procedure call protocol encoded in JSON.

**PAP Integration**: PAP-Hooks profile uses JSON-RPC 2.0 over WebSocket/SSE for open I/O operations.

### [4] OAuth 2.1

**Author**: IETF OAuth Working Group
**Status**: Draft
**URL**: https://oauth.net/2.1/

**Summary**: Authorization framework consolidating OAuth 2.0 best practices with mandatory PKCE and security improvements.

**PAP Integration**: PAP-Hooks uses OAuth 2.1 with JWT bearer tokens for authentication.

---

## Standards and RFCs

### RFC 9110: HTTP Semantics

**URL**: https://datatracker.ietf.org/doc/html/rfc9110

**Relevance**: PAP error codes align with HTTP semantics (200, 202, 400-series, 500-series) while extending for agent-specific scenarios (480-482).

### RFC 8446: TLS 1.3

**URL**: https://datatracker.ietf.org/doc/html/rfc8446

**Relevance**: PAP-CP requires TLS 1.3 with mutual authentication (mTLS) for all control plane connections.

### RFC 8032: Ed25519 Signatures

**URL**: https://datatracker.ietf.org/doc/html/rfc8032

**Relevance**: PAP uses Ed25519 for message signing on all PAP-CP control messages, providing replay protection.

### RFC 2136: DNS UPDATE

**URL**: https://datatracker.ietf.org/doc/html/rfc2136

**Relevance**: PAP uses DNS UPDATE for dynamic agent addressing (`{agent}.{region}.a.plugged.in`) with wildcard TLS certificates.

### OpenTelemetry Specification

**URL**: https://opentelemetry.io/docs/specs/otel/

**Relevance**: PAP messages carry `trace_id` and `span_id` for distributed tracing; all components emit OpenTelemetry spans.

---

## Agent Systems Research

### [5] Fundamentals of Building Autonomous LLM Agents

**Authors**: V. de Lamo Castrillo, H. K. Gidey, A. Lenz, A. Knoll
**Reference**: arXiv:2510.09244, 2025
**URL**: https://arxiv.org/abs/2510.09244

**Key Findings**:
- Documents gaps between human performance (>72%) and state-of-the-art agents (~43% on OSWorld)
- Identifies perception-reasoning-memory-action framework failures
- Highlights need for ops-grade lifecycle management

**PAP Contribution**: Addresses systematic failures through:
- Perception: Controlled via provisioned MCP servers and tool policies
- Reasoning: Loop detection via heartbeat monitoring
- Memory: Versioned state management with audit trails
- Action: Sandboxed execution with credential-based access control

### [6] Multi-Agent Collaboration Mechanisms: A Survey of LLMs

**Authors**: H. Tran, et al.
**Reference**: arXiv:2501.06322, 2025
**URL**: https://arxiv.org/abs/2501.06322

**Key Findings**:
- Systematic failures in cascading errors when agents lack proper lifecycle management
- Need for explicit coordination protocols

**PAP Contribution**: Provides protocol-level coordination through lifecycle states, ownership transfer, and A2A integration.

---

## Multi-Agent Coordination

### [7] Multi-Agent Coordination via Multi-Level Communication

**Authors**: Y. Ding, et al.
**Reference**: Proceedings of NeurIPS 2024

**Key Findings**:
- Importance of hierarchical communication patterns
- Control plane vs. data plane separation

**PAP Contribution**: Dual-profile architecture (PAP-CP for control, PAP-Hooks for data) directly addresses multi-level communication needs.

---

## Security and Trust

### [8] Security of AI Agents

**Authors**: Y. He, et al.
**Reference**: arXiv:2406.08689v2, 2024
**URL**: https://arxiv.org/abs/2406.08689

**Key Findings**:
- Threat models for autonomous agents
- Authentication, authorization, and audit requirements
- Attack vectors: replay attacks, credential theft, state manipulation

**PAP Contribution**: Comprehensive security model with:
- Mutual TLS (mTLS) for PAP-CP
- Ed25519 signatures with nonce-based replay protection
- OAuth 2.1 for PAP-Hooks
- Immutable audit trails

### [9] TRiSM for Agentic AI

**Full Title**: Trust, Risk, and Security Management in LLM-based Multi-Agent Systems
**Reference**: arXiv:2506.04133v1, 2025
**URL**: https://arxiv.org/abs/2506.04133

**Key Findings**:
- Trust frameworks for agent ecosystems
- Risk assessment methodologies
- Compliance and governance patterns

**PAP Contribution**: Station authority model provides centralized trust anchor; ownership transfer enables risk migration; audit trails support compliance.

---

## Governance and Compliance

### [10] MI9 - Agent Intelligence Protocol

**Full Title**: Runtime Governance for Agentic AI Systems
**Reference**: arXiv:2508.03858v1, 2025
**URL**: https://arxiv.org/abs/2508.03858

**Key Findings**:
- Need for runtime governance mechanisms
- Policy enforcement at protocol level
- Observable and auditable agent behavior

**PAP Contribution**: Station-held kill authority, policy bundles during provisioning, immutable audit logs, and lifecycle state enforcement.

---

## Protocol Interoperability

### [11] A Survey of Agent Interoperability Protocols

**Full Title**: MCP, ACP, A2A, and ANP
**Reference**: arXiv:2505.02279v1, 2025
**URL**: https://arxiv.org/abs/2505.02279

**Key Findings**:
- Comparison of existing agent protocols
- Gaps in lifecycle management and governance
- Need for complementary rather than competing protocols

**PAP Contribution**: Designed as complementary to MCP (tool access) and A2A (peer delegation) by focusing on lifecycle substrate—the layer below orchestration logic.

---

## BibTeX Entries

### Primary Paper

```bibtex
@misc{karaca2025pap,
  title={The Plugged.in Agent Protocol (PAP): A Comprehensive Framework for Autonomous Agent Lifecycle Management},
  author={Karaca, Cem},
  year={2025},
  note={Draft v0.3 for arXiv cs.DC},
  publisher={VeriTeknik and Plugged.in},
  url={https://github.com/VeriTeknik/PAP},
  keywords={autonomous agents, control plane, lifecycle management, mTLS, OAuth 2.1, JSON-RPC, gRPC, Ed25519, audit, DNS, ownership transfer, heartbeat, telemetry, MCP, A2A, interoperability}
}
```

### Agent Systems

```bibtex
@misc{delamo2025autonomous,
  title={Fundamentals of Building Autonomous LLM Agents},
  author={de Lamo Castrillo, V. and Gidey, H. K. and Lenz, A. and Knoll, A.},
  year={2025},
  eprint={2510.09244},
  archivePrefix={arXiv},
  primaryClass={cs.AI}
}

@misc{tran2025collaboration,
  title={Multi-Agent Collaboration Mechanisms: A Survey of LLMs},
  author={Tran, H. and others},
  year={2025},
  eprint={2501.06322},
  archivePrefix={arXiv},
  primaryClass={cs.MA}
}
```

### Security

```bibtex
@misc{he2024security,
  title={Security of AI Agents},
  author={He, Y. and others},
  year={2024},
  eprint={2406.08689},
  archivePrefix={arXiv},
  primaryClass={cs.CR},
  note={Version 2}
}

@misc{trism2025agentic,
  title={TRiSM for Agentic AI: Trust, Risk, and Security Management in LLM-based Multi-Agent Systems},
  author={TRiSM Consortium},
  year={2025},
  eprint={2506.04133},
  archivePrefix={arXiv},
  primaryClass={cs.CR}
}
```

### Governance

```bibtex
@misc{mi9-2025,
  title={MI9 - Agent Intelligence Protocol: Runtime Governance for Agentic AI Systems},
  author={MI9 Protocol Team},
  year={2025},
  eprint={2508.03858},
  archivePrefix={arXiv},
  primaryClass={cs.DC}
}
```

### Interoperability

```bibtex
@misc{interop2025survey,
  title={A Survey of Agent Interoperability Protocols: MCP, ACP, A2A, and ANP},
  author={Protocol Survey Authors},
  year={2025},
  eprint={2505.02279},
  archivePrefix={arXiv},
  primaryClass={cs.DC}
}
```

### Protocol Specifications

```bibtex
@techreport{mcp2025,
  title={Model Context Protocol Specification},
  author={Anthropic},
  year={2025},
  institution={Anthropic},
  url={https://modelcontextprotocol.io/specification/2025-06-18/},
  note={Version 2025-06-18}
}

@techreport{a2a2025,
  title={Agent-to-Agent Protocol (A2A) Specification},
  author={{Linux Foundation}},
  year={2025},
  version={0.3.0},
  institution={Linux Foundation},
  url={https://a2a-protocol.org/latest/specification/}
}
```

---

## Citation Guidelines

When citing PAP in academic work, use the primary paper citation and reference specific technical documents as needed:

**Primary citation**:
```
Karaca, C. (2025). The Plugged.in Agent Protocol (PAP): A Comprehensive
Framework for Autonomous Agent Lifecycle Management. Draft v0.3 for arXiv cs.DC.
VeriTeknik & Plugged.in. https://github.com/VeriTeknik/PAP
```

**Technical specifications**:
```
PAP-RFC-001 v1.0: Plugged.in Agent Protocol Specification.
https://github.com/VeriTeknik/PAP/blob/main/docs/rfc/pap-rfc-001-v1.0.md
```

---

## Document Maintenance

This references document is maintained as the single source of truth for PAP citations. When adding new references:

1. Add to appropriate category section
2. Include BibTeX entry
3. Note PAP integration/relevance
4. Update cross-references in other documents to point here

**Maintainer**: PAP Core Team
**Last Review**: November 12, 2025
**Next Review**: January 2026 (or upon submission to arXiv)

---

**Related Documents**:
- `pap-rfc-001-v1.0.md` - Complete protocol specification
- `evaluation-methodology.md` - Benchmarking and performance testing
- `overview.md` - Vision and architectural philosophy
