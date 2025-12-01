# Changelog

All notable changes to the Plugged.in Agent Protocol (PAP) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2024-12-01

### 🎉 Initial Stable Release - "Autonomy Without Anarchy"

The first stable release of the Plugged.in Agent Protocol (PAP), establishing the foundational framework for autonomous agent lifecycle management.

### Added

#### Core Protocol (PAP-RFC-001 v1.0)
- **Dual-Profile Architecture**: PAP-CP (gRPC/mTLS for control plane) + PAP-Hooks (JSON-RPC/OAuth for ecosystem integration)
- **Normative Lifecycle States**: `NEW → PROVISIONED → ACTIVE ↔ DRAINING → TERMINATED` (+ `KILLED`)
- **Zombie-Prevention**: Strict heartbeat/metrics separation prevents control plane saturation
- **Protocol Buffers Schema**: Complete `pap.proto` with all message types

#### Heartbeat System
- Three operational modes: `EMERGENCY` (5s), `IDLE` (30s), `SLEEP` (15min)
- Liveness-only payloads (mode + uptime_seconds only)
- NO resource data in heartbeats (CPU/memory goes to separate metrics channel)

#### Metrics Telemetry
- Separate channel from heartbeats (zombie prevention)
- Supports: `cpu_percent`, `memory_mb`, `requests_handled`, `custom_metrics`
- 60-second default interval (independent of heartbeat mode)

#### Security
- Ed25519 message signing REQUIRED for PAP-CP
- mTLS for all control plane communication
- Nonce-based replay protection (≥60s cache)
- OAuth 2.1 + JWT for PAP-Hooks

#### DNS-Based Identity
- Pattern: `{agent}.{cluster}.a.plugged.in`
- DNSSEC REQUIRED for trust chain
- Certificate SAN alignment with DNS entries

#### Error Codes
- Standardized codes aligned with HTTP semantics
- Agent-specific: `AGENT_UNHEALTHY` (480), `AGENT_BUSY` (481), `DEPENDENCY_FAILED` (482)

### Documentation
- **PAP-RFC-001 v1.0**: Complete protocol specification
- **PAP-Hooks Spec**: JSON-RPC 2.0 open I/O profile
- **Service Registry**: DNS-based agent discovery
- **Ownership Transfer**: Agent migration protocol
- **Deployment Guide**: Kubernetes/Traefik reference architecture
- **Evaluation Methodology**: Performance targets and benchmarking
- **Academic Paper**: Draft v0.3 for arXiv cs.DC

### SDK Scaffolding
- TypeScript SDK structure
- Python SDK structure
- Go SDK structure
- Rust SDK structure

### Protocol Interoperability
- MCP tool integration support
- A2A peer communication support
- OpenTelemetry tracing (`trace_id`, `span_id`)

### Companion Projects

#### Compass Agent (First Reference Implementation)
- AI Jury/Oracle for multi-model consensus
- TF-IDF semantic similarity consensus engine
- Verdict types: `unanimous`, `split`, `no_consensus`
- PAP-RFC-001 compliant heartbeat/metrics

#### Model Router API
- OpenAI-compatible chat completions gateway
- Unified API for OpenAI, Anthropic, Google
- Automatic provider routing
- Streaming support

---

## PAP-RFC-001-rev2.1 — 2025-11-01

- Envelope: added `trace_id` and `span_id` for OpenTelemetry correlation (proto + SDK types).
- README: clarified heartbeat is liveness-only; added DNS topology; added error code summary; added observability note.
- RFC: added rev2.1 document with DNS delegation, tracing, and heartbeat semantics.
- Examples: added separate heartbeat and metrics examples for Python and TypeScript.
- Tooling: added `Makefile` and `proto/buf.yaml`.
- Governance: added `CODE_OF_CONDUCT.md` and `SECURITY.md`; referenced in README.

## Earlier
- Scaffolding for PAP v1 transport, message families, and docs.

