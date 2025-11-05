# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Version**: PAP v1.0 (Paper-Aligned)
**Status**: Stable Candidate
**Last Updated**: November 4, 2025

PAP (Plugged.in Agent Protocol) is a comprehensive framework for autonomous agent lifecycle management, establishing Plugged.in as the central authority for creating, configuring, and controlling autonomous agents while enabling distributed operation through open protocols.

**Core Architecture Metaphor**: Space station (Station) controlling autonomous spacecraft (Satellites) - maintaining autonomy while preserving oversight.

**Guiding Principle**: "Autonomy without anarchy" - agents run independently but the Station retains absolute oversight for provisioning, heartbeat supervision, ownership management, and emergency termination.

**Why PAP Matters**: Unlike MCP, ACP, and A2A which focus on tool invocation and orchestration logic, PAP defines the physical and logical substrate - how agents live, breathe, migrate, and die across infrastructure. It merges operational DevOps controls with cognitive AI design.

## Key Innovations (v1.0)

1. **Dual-Profile Architecture**: PAP-CP (Control Plane) for ops-grade control; PAP-Hooks (Open I/O) for vendor-neutral ecosystem integration
2. **Zombie-Prevention Superpower**: Strict heartbeat/metrics separation prevents control plane saturation
3. **Normative Lifecycle States**: NEW → PROVISIONED → ACTIVE ↔ DRAINING → TERMINATED (+ KILLED)
4. **Protocol Interoperability**: Native support for MCP tools and A2A peer communication
5. **Comprehensive Security**: Dual authentication (mTLS + OAuth 2.1), Ed25519 signatures, credential rotation

## Repository Structure

### Documentation (`docs/`)
- **`overview.md`**: Mission, vision, dual-profile architecture, and protocol innovations
- **`rfc/pap-rfc-001-v1.0.md`**: Complete PAP v1.0 specification (paper-aligned)
- **`pap-hooks-spec.md`**: JSON-RPC 2.0 open I/O profile specification
- **`service-registry.md`**: DNS-based agent discovery and capability advertisement
- **`ownership-transfer.md`**: Agent migration protocol between Stations
- **`deployment-guide.md`**: Kubernetes/Traefik reference deployment

### Protocol Definitions (`proto/`)
- **`pap/v1/pap.proto`**: Protocol Buffers v3 schema with lifecycle messages
  - PAP-CP messages: Provision, Invoke, Heartbeat, Metrics, Terminate, Transfer
  - Strict heartbeat/metrics separation (CRITICAL)
  - Lifecycle state definitions

### SDKs (`sdk/`)
- **TypeScript**: (Planned) PAP-CP and PAP-Hooks client libraries
- **Python**: (Planned) PAP-CP and PAP-Hooks client libraries
- **Rust**: (Planned) High-performance client libraries
- **Go**: (Planned) Cloud-native client libraries

### Services
- **`proxy/`**: Gateway with PAP-CP ↔ PAP-Hooks translation
- **`registry/`**: Service Registry for DNS-based agent discovery
- **`ops/`**: Operational runbooks, SLO definitions, monitoring

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

### Dual-Profile Architecture

#### PAP-CP (Control Plane) Profile
- **Transport**: gRPC over HTTP/2 with TLS 1.3
- **Authentication**: Mutual TLS (mTLS) REQUIRED
- **Wire Format**: Protocol Buffers v3
- **Message Security**: Ed25519 signatures REQUIRED
- **Replay Protection**: Nonce cache ≥60 seconds REQUIRED
- **Use Cases**: Provisioning, lifecycle control, heartbeats, metrics, termination
- **Endpoint**: `grpc://pap.plugged.in:50051`

#### PAP-Hooks (Open I/O) Profile
- **Transport**: JSON-RPC 2.0 over WebSocket or HTTP SSE
- **Authentication**: OAuth 2.1 with JWT RECOMMENDED
- **Wire Format**: UTF-8 JSON with schema validation
- **Message Security**: JOSE/JWT signing OPTIONAL
- **Use Cases**: Tool invocations, MCP access, A2A delegation, external APIs
- **Endpoint**: `wss://{agent}.{region}.a.plugged.in/hooks`

**Gateway Translation**: Gateways MAY translate between profiles for ecosystem interoperability.

### Zombie Prevention: The Superpower

**CRITICAL**: PAP v1.0 enforces **strict heartbeat/metrics separation**. This is the zombie-prevention superpower.

#### Heartbeat (Liveness Only)
- **Payload**: Mode (EMERGENCY/IDLE/SLEEP), uptime_seconds
- **FORBIDDEN**: CPU, memory, or any resource data
- **Intervals**:
  - EMERGENCY: 5 seconds
  - IDLE: 30 seconds (default)
  - SLEEP: 15 minutes
- **Detection**: One missed interval → AGENT_UNHEALTHY (480)

#### Metrics (Resource Telemetry - Separate Channel)
- **Payload**: cpu_percent, memory_mb, requests_handled, custom_metrics
- **Channel**: Separate from heartbeats
- **Frequency**: Independent (typically 60s)

**Why This Matters**: Large telemetry payloads cannot starve the control path. This enables aggressive zombie detection without false positives.

**Kill Authority**: Exclusively reserved for Station via signed `force_kill` control messages.

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

### Heartbeat Requirements (PAP-RFC-001 v1.0)

**CRITICAL CHANGE from earlier versions**: Heartbeats are now liveness-only!

- **Mode**: EMERGENCY (5s), IDLE (30s), or SLEEP (15min)
- **Required fields**: `mode`, `uptime_seconds` ONLY
- **FORBIDDEN fields**: NO cpu_percent, memory_mb, or resource data
- **Failure threshold**: Missing 1 heartbeat interval triggers `AGENT_UNHEALTHY (480)`
- **Escalation**: Station may invoke `force_kill` based on policy

**Resource telemetry** MUST use separate `MetricsReport` message on independent channel.

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

### ✅ Completed (v1.0)
- Dual-profile architecture (PAP-CP + PAP-Hooks)
- Protocol Buffer schema with lifecycle messages
- Strict heartbeat/metrics separation
- Normative lifecycle states and transitions
- Ownership transfer protocol
- Comprehensive error codebook
- Service Registry schema
- DNS-based addressing with DNSSEC
- Deployment reference (Kubernetes/Traefik)

### 🔄 In Progress
- SDK implementations (TypeScript, Python, Rust, Go)
- Gateway with PAP-CP ↔ PAP-Hooks translation
- Station with provisioning and lifecycle management
- Conformance test suite

### 📋 Planned (v1.1+)
- Multi-region active-active Station deployment
- Asynchronous state replication (CRDTs)
- Federated identity with DIDs
- Advanced policy DSL
- Formal verification (TLA+)

## References

- **Main Specification**: `docs/rfc/pap-rfc-001-v1.0.md` - Complete PAP v1.0 specification (paper-aligned)
- **PAP-Hooks Spec**: `docs/pap-hooks-spec.md` - JSON-RPC 2.0 open I/O profile
- **Service Registry**: `docs/service-registry.md` - DNS-based agent discovery
- **Ownership Transfer**: `docs/ownership-transfer.md` - Agent migration protocol
- **Deployment Guide**: `docs/deployment-guide.md` - Kubernetes reference deployment
- **Vision Document**: `docs/overview.md` - Mission, vision, and architectural philosophy
- **Wire Schema**: `proto/pap/v1/pap.proto` - Protocol Buffers v3 definitions

## Current Status

**Version**: PAP v1.0 (Paper-Aligned)
**Status**: Stable Candidate

The repository now contains comprehensive specifications for PAP v1.0, including dual-profile architecture, strict heartbeat/metrics separation, normative lifecycle states, and deployment references.

**Key Achievement**: The zombie-prevention superpower via strict heartbeat/metrics separation is fully specified and ready for implementation.

SDK implementations, Gateway service, and Station service are planned next. See roadmap above for details.
