# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PAP (Plugged.in Agent Protocol) is a control and telemetry protocol connecting Plugged.in's core control plane (the Station) with autonomous agents (Satellites). The protocol defines authentication, command exchange, telemetry streaming, lifecycle management, and centralized policy enforcement.

**Core Architecture Metaphor**: Space station (Station) controlling autonomous spacecraft (Satellites) - maintaining autonomy while preserving oversight.

**Guiding Principle**: "Autonomy without anarchy" - agents run independently but the Station retains absolute oversight for provisioning, heartbeat supervision, ownership management, and emergency termination.

**Why PAP Matters**: Unlike MCP, ACP, and A2A which focus on tool invocation and orchestration logic, PAP defines the physical and logical substrate - how agents live, breathe, migrate, and die across infrastructure. It merges operational DevOps controls with cognitive AI design.

## Repository Structure

- **`docs/`**: Protocol specifications and architecture documentation
  - `overview.md`: Mission, vision, roles, and roadmap
  - `rfc/pap-rfc-001.md`: Canonical transport specification (handshake, message schema, lifecycle flows, security)
- **`proto/`**: Protocol Buffers v1 schema definitions
  - `pap/v1/pap.proto`: Wire format for all PAP messages
- **`sdk/`**: Language-specific client/server implementations (planned: TypeScript, Python, Rust, Go)
- **`proxy/`**: PAP Proxy service plans (mTLS termination, routing, policy enforcement)
- **`registry/`**: Identity, policy, and capability management service plans
- **`ops/`**: Operational runbooks, SLO definitions, heartbeat policies

## Protocol Architecture

### Core Components

- **Station**: Plugged.in control plane with lifecycle authority, routing, policy enforcement, and kill authority
- **Satellite**: Autonomous agents that execute missions, emit telemetry, self-heal, and respect Station mandates
- **Proxy** (`mcp.plugged.in`): Frontdoor terminating TLS, validating signatures, enforcing quotas, logging all traffic

### Identity & Addressing

- DNS-based identity: `{agent}.{cluster}.a.plugged.in`
- Platform: Kubernetes (Rancher managed) + Traefik ingress with wildcard TLS
- Authentication: JWT onboarding tokens → long-lived X.509 client certificates
- DNSSEC required for identity verification

### Message Families

1. **invoke**: Commands from Station or peer Satellites
2. **response**: Synchronous/async acknowledgments with optional streaming
3. **event**: Telemetry (heartbeats, logs, alerts, metrics)
4. **error**: Structured failure reports with standardized codes

### Security Model

- Transport: HTTP/2 over TLS 1.3 with mutual authentication (mTLS)
- Payload signing: Ed25519 signatures covering headers and body
- Replay protection: Nonce cache with 15-minute expiry
- Key rotation: At least every 90 days
- Audit trail: Immutable append-only storage via Memory service

### Autonomy Benefits

- **Performance**: Agents act instantly without waiting for orchestration lag
- **Fault Isolation**: Each agent sandboxed; one crash doesn't cascade
- **Specialization**: Dedicated agents for memory, analytics, edge collection, focus, etc.

### Zombie Prevention

A "zombie" is an unresponsive or resource-hogging process pretending to be alive. PAP prevents this via:

- **Continuous heartbeats**: Agents report liveness, CPU/MEM load every 10s (default)
- **Watchdog thresholds**: Missing 3 consecutive heartbeats triggers escalation
- **Kill authority**: Exclusively reserved for Station via signed `force_kill` control messages
- **Resource monitoring**: CPU %, memory MB, active jobs tracked in heartbeat payload

## Transport & Protocol Binding

- **Canonical Binding**: gRPC over HTTP/2 with TLS 1.3
- **Endpoint**: `pap.plugged.in:443` (default), regional variants: `{region}.pap.plugged.in`
- **Alternative Bindings**: Alternative bindings MUST maintain identical semantics to gRPC
- **Rate Limiting**: Proxy enforces rate limits and returns `RATE_LIMITED` (429) for violations
- **Streaming**: Supports chunked responses for large payloads (>10 MB must stream)

## Working with Protobuf

### Generating Code

```bash
# Install protoc 3.21+ and language-specific plugins first
protoc --proto_path=. \
  --go_out=../sdk/go --go_opt=paths=source_relative \
  --python_out=../sdk/python \
  pap/v1/pap.proto
```

### Schema Evolution

- Maintain backward compatibility within `v1` package
- Breaking changes require new package version (e.g., `pap.v2`)
- Document lifecycle invariants and validation expectations in proto comments
- Commit generated code to SDK language-specific subdirectories

## Lifecycle Management

### Provisioning Flow

1. Satellite submits JWT onboarding token
2. Station issues certificate, DNS entry, policy bundle
3. Satellite registers heartbeat interval and syncs initial state

### Heartbeat Requirements (PAP-RFC-001 §8)

- **Interval**: Default 10 seconds (negotiable)
- **Required fields**: `cpu_percent`, `memory_mb`, `uptime_seconds`, `active_jobs`
- **Failure threshold**: Missing 3 consecutive heartbeats triggers `AGENT_UNHEALTHY`
- **Escalation**: Station may invoke `force_kill` based on policy

### Termination

- **Graceful**: `invoke` with method `terminate` → agent drains work, ACKs, disconnects
- **Force kill**: Signed `force_kill` directive → Proxy revokes cert → infrastructure terminates process

### Ownership Transfer

1. Current Station publishes transfer intent with time-bound authorization
2. Receiving Station validates state snapshot
3. Satellite re-handshakes with new Station; old credentials revoked

## Error Code Standards

Standardized error codes align with HTTP semantics but extend for agent-specific scenarios:

| Code | HTTP | Usage |
|------|------|-------|
| `AGENT_UNHEALTHY` | 480 | Heartbeat anomaly detected |
| `AGENT_BUSY` | 481 | Agent overloaded; retry later |
| `DEPENDENCY_FAILED` | 482 | Downstream call failed |
| `VERSION_UNSUPPORTED` | 505 | Protocol version mismatch |

See `docs/rfc/pap-rfc-001.md` §10 for full error code table.

## SDK Development Requirements

All language SDKs must provide:

- Envelope signing/verification helpers (Ed25519 preferred)
- Heartbeat emitters with pluggable health probes
- Retry-aware `invoke` helpers with deadline propagation
- Structured error mapping to PAP `ErrorCode`
- Conformance tests exercising handshake, invoke, event, and lifecycle flows

## Capabilities System

Capabilities are declarative statements about supported features:

- Format: `{family}.{feature}` (e.g., `invoke.async`, `event.heartbeat`, `lifecycle.transfer`)
- Declared during handshake
- Station rejects handshakes missing required capabilities for policy domain
- Stored in Registry service for routing and enforcement

## Development Principles

### Repository State

**IMPORTANT**: This is a greenfield project. Currently only contains:

- Documentation and specifications (`docs/`, READMEs)
- Protocol Buffer schema (`proto/pap/v1/pap.proto`)
- No implementation code exists yet

When adding implementation code, ensure `.gitignore` is updated for:

- Generated protobuf code (language-specific stubs)
- Language-specific artifacts (node_modules, **pycache**, target/, go.sum, etc.)
- Build outputs and binaries
- IDE/editor files (.vscode, .idea, etc.)
- Environment files (.env, .env.local)
- Certificates and keys (\*.pem, \*.key, \*.crt)

### Documents Scoping

- Documents should only be scoped by `project_uuid` (Hub level)

### Database Migrations

- **Never** apply migrations directly to the database
- Use `pnpm db:generate` and `pnpm db:migrate` for repeatable solutions
- Maintain migration history in version control

### Security

- **Never** expose `.env` keys to GitHub or commits
- Always use mutual TLS for PAP communications
- Verify signatures on all incoming messages before processing
- Implement replay protection using nonce cache

### Branching Strategy

- Create new branch for implementation work before starting
- Align proposal discussions with RFC structure under `docs/rfc/`

## Observability & Telemetry

- **Proxy**: Must emit OpenTelemetry traces with envelope identifiers
- **Satellites**: Should expose structured logs for `invoke` handlers
- **Station**: Maintains immutable audit trails in append-only storage
- **Metrics**: Custom gauges in heartbeat payload, MetricBatch events

## Compliance Checklist (PAP-RFC-001 §13)

Before deploying PAP implementations, verify:

- [ ] Handshake negotiation implemented
- [ ] Heartbeat emission and watchdog handling
- [ ] Error code mapping to local exceptions
- [ ] Signature and hash verification on every message
- [ ] Replay protection and nonce cache
- [ ] Policy enforcement for lifecycle directives

## Implementation Roadmap

1. **PAP v1.0 Schema**: Protobuf schema, standardized codes, handshake spec (IN PROGRESS)
2. **SDKs**: TypeScript, Python, Rust, Go with signing, retry, telemetry helpers (PLANNED)
3. **Proxy**: mTLS router, JWT verification, OpenTelemetry logs at `mcp.plugged.in` (PLANNED)
4. **Registry & Policy Layer**: Capabilities, routes, IAM-like control (PLANNED)
5. **Marketplace Integration**: Helm charts, manifests, deployment audit (PLANNED)

## References

- **Primary Spec**: `docs/rfc/pap-rfc-001.md` - Canonical transport contract
- **Vision Document**: `docs/overview.md` - Mission and architectural philosophy
- **Wire Schema**: `proto/pap/v1/pap.proto` - Protocol Buffers v1 definitions
- **Extended Context**: `pap_plugged (3).md` - Detailed protocol motivation and comparison with MCP/ACP/A2A

## Current Status

This repository contains initial scaffolding for PAP v1.0. Specifications are in draft form. SDK implementations, Proxy service, and Registry service are planned but not yet built.
