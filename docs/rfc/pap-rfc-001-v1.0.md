# PAP-RFC-001 v1.0 — Plugged.in Agent Protocol

**Status**: Stable Candidate
**Protocol Version**: PAP v1.0 (Paper-Aligned)
**Paper Version**: Draft v0.3 (for arXiv cs.DC)
**Revision**: 1.0
**Date**: November 12, 2025
**Author**: Cem Karaca (VeriTeknik & Plugged.in)
**Audience**: Station developers, Agent implementers, Infrastructure teams

This specification defines the Plugged.in Agent Protocol (PAP) v1.0, a comprehensive framework for autonomous agent lifecycle management. This version introduces the dual-profile architecture and aligns with the PAP academic paper submitted for publication in arXiv cs.DC.

**Academic Paper**: "The Plugged.in Agent Protocol (PAP): A Comprehensive Framework for Autonomous Agent Lifecycle Management" by Cem Karaca, Draft v0.3 for arXiv cs.DC, November 2025.

---

## 1. Introduction and Scope

### 1.1 Purpose

PAP establishes Plugged.in as the central authority for creating, configuring, and controlling autonomous agents while enabling distributed operation through open protocols. The protocol addresses critical gaps in agent reliability, governance, and interoperability identified in production deployments.

### 1.2 Design Philosophy

**"Autonomy without anarchy"** - Agents operate independently with their own memory, tools, and decision-making capabilities, yet remain under organizational governance through protocol-level controls.

### 1.3 Key Contributions

1. **Dual-Profile Architecture**: PAP-CP for secure control plane; PAP-Hooks for open ecosystem
2. **Strict Heartbeat/Telemetry Separation**: Liveness-only heartbeats prevent control plane saturation
3. **Comprehensive Lifecycle Management**: Normative states with Station-held kill authority
4. **Protocol Interoperability**: Native support for MCP tools and A2A peer communication

---

## 2. Architecture Overview

### 2.1 System Entities

**Station** (Plugged.in Control Plane)
- Provisions agents with credentials and configuration
- Manages lifecycle states and transitions
- Enforces policies and quotas
- Maintains audit logs
- Holds exclusive termination authority

**Agent** (Autonomous Executor)
- Executes tasks independently
- Maintains local state and context
- Accesses tools via MCP servers
- Communicates with peers via A2A
- Reports liveness through heartbeats

**Gateway** (Protocol Mediator)
- Translates between PAP-CP and PAP-Hooks
- Enforces rate limits and quotas
- Validates signatures and tokens
- Maintains circuit breakers
- Provides observability hooks

### 2.2 Protocol Profiles

PAP defines two complementary profiles:

#### PAP-CP (Control Plane) Profile

- **Transport**: gRPC over HTTP/2 with TLS 1.3
- **Authentication**: Mutual TLS (mTLS) REQUIRED
- **Wire Format**: Protocol Buffers v3
- **Message Security**: Ed25519 signatures REQUIRED
- **Replay Protection**: Nonce cache ≥60 seconds REQUIRED
- **Use Cases**: Provisioning, lifecycle control, heartbeats, metrics, termination

#### PAP-Hooks (Open I/O) Profile

- **Transport**: JSON-RPC 2.0 over WebSocket or HTTP SSE
- **Authentication**: OAuth 2.1 with JWT RECOMMENDED
- **Wire Format**: UTF-8 JSON with schema validation
- **Message Security**: JOSE/JWT signing OPTIONAL
- **Use Cases**: Tool invocations, MCP access, A2A delegation, external APIs

**Gateway Translation**: Gateways MAY translate between profiles while preserving semantics.

---

## 3. Transport and Wire Protocol

### 3.1 PAP-CP Transport (Normative)

**Endpoint Format**: `grpc://{station-host}:50051` (default)
- Primary: `grpc://pap.plugged.in:50051`
- Regional: `grpc://{region}.pap.plugged.in:50051`

**TLS Requirements**:
- TLS 1.3 REQUIRED
- Mutual TLS (mTLS) REQUIRED
- Certificate validation REQUIRED
- Certificate pinning RECOMMENDED

**Message Structure**:
```protobuf
message PAPMessage {
  Header header = 1;
  oneof payload {
    ProvisionRequest provision = 2;
    InvokeRequest invoke = 4;
    HeartbeatEvent heartbeat = 6;
    MetricsReport metrics = 7;
    TerminateRequest terminate = 8;
    // ... (see proto/pap/v1/pap.proto)
  }
  bytes signature = 15;  // Ed25519 (REQUIRED)
  bytes checksum = 16;   // SHA-256 (REQUIRED)
}

message Header {
  string version = 1;      // "pap-cp/1.0"
  string agent_uuid = 2;   // "namespace/agent@v1.0"
  string station_id = 3;   // "plugged.in"
  string instance_id = 4;  // Per-process UUID
  int64 timestamp = 5;     // Unix microseconds
  bytes nonce = 6;         // 32-byte random (REQUIRED)
  string trace_id = 7;     // OpenTelemetry trace ID
  string span_id = 8;      // OpenTelemetry span ID
}
```

### 3.2 PAP-Hooks Transport (Normative)

**Endpoint Format**: `wss://{agent}.{region}.a.plugged.in/hooks`

**WebSocket Connection**:
```javascript
{
  "jsonrpc": "2.0",
  "id": "req-12345",
  "method": "tool.invoke",
  "params": {
    "tool": "web-search",
    "arguments": {"query": "quantum computing"},
    "context": {
      "agent_uuid": "namespace/agent@v1.0",
      "trace_id": "trace-xyz",
      "authorization": "Bearer {jwt-token}"
    }
  }
}
```

See `docs/pap-hooks-spec.md` for complete PAP-Hooks specification.

---

## 4. Identity and Addressing

### 4.1 DNS-Based Identity

Agents are addressed as: `{agent}.{region}.a.plugged.in`

**Examples**:
- `research.us-east.a.plugged.in`
- `memory.eu-west.a.plugged.in`
- `focus.ap-south.a.plugged.in`

### 4.2 DNS Delegation

```bind
; Delegation in plugged.in zone
a.plugged.in.    IN    NS    ns1.plugged.in.
a.plugged.in.    IN    NS    ns2.plugged.in.

; Wildcard records for regions
*.us-east.a.plugged.in.    IN    CNAME    ingress-us-east.plugged.in.
*.eu-west.a.plugged.in.    IN    CNAME    ingress-eu-west.plugged.in.
```

### 4.3 Certificate Management

- **Certificate Authority**: Plugged.in CA
- **Certificate Type**: X.509 v3 with Ed25519 signatures
- **SANs**: MUST include agent FQDN
- **Validity**: Default 90 days, auto-renewal before 30-day expiry
- **Revocation**: OCSP stapling REQUIRED

---

## 5. Lifecycle States and Transitions

### 5.1 State Machine (Normative)

```
NEW → PROVISIONED → ACTIVE ↔ DRAINING → TERMINATED
                        ↓ (error)
                      KILLED
```

### 5.2 State Definitions

| State | Description | Transitions |
|-------|-------------|-------------|
| **NEW** | Agent created, awaiting provisioning | → PROVISIONED |
| **PROVISIONED** | Credentials issued, not yet operational | → ACTIVE |
| **ACTIVE** | Operational, handling requests | ↔ DRAINING, → KILLED |
| **DRAINING** | Graceful shutdown, completing tasks | → TERMINATED, → KILLED |
| **TERMINATED** | Clean shutdown completed | (final) |
| **KILLED** | Force-killed by Station | (final) |

### 5.3 Transition Triggers

**NEW → PROVISIONED**:
- Trigger: Successful `ProvisionRequest` processing
- Requirements: Valid invite token, credential issuance

**PROVISIONED → ACTIVE**:
- Trigger: First successful heartbeat + handshake acknowledgment
- Requirements: Valid credentials, capability negotiation complete

**ACTIVE ↔ DRAINING**:
- Trigger: `TerminateRequest` with grace period
- Requirements: Agent acknowledgment, task drain initiation

**DRAINING → TERMINATED**:
- Trigger: All tasks completed OR grace period expired
- Requirements: Final status report

**ANY → KILLED**:
- Trigger: `ForceKill` directive OR critical heartbeat failure
- Authority: Station ONLY
- Requirements: Signed control message

---

## 6. Heartbeat vs. Metrics (Zombie Prevention)

### 6.1 The Separation Rule (Normative)

**CRITICAL**: Heartbeats carry **liveness only**. Resource data is **FORBIDDEN** in heartbeats.

**HeartbeatEvent Message**:
```protobuf
message HeartbeatEvent {
  Header header = 1;
  HeartbeatMode mode = 2;      // EMERGENCY, IDLE, or SLEEP
  uint64 uptime_seconds = 3;    // Process uptime
  // NO OTHER FIELDS ALLOWED
}
```

### 6.2 Heartbeat Intervals

| Mode | Interval | Use Case |
|------|----------|----------|
| **EMERGENCY** | 5 seconds | Critical state, requires immediate attention |
| **IDLE** | 30 seconds | Normal operation |
| **SLEEP** | 15 minutes | Low activity, background tasks |

### 6.3 Zombie Detection

**Detection Rule**: One missed heartbeat interval → `AGENT_UNHEALTHY (480)`

Agents that miss their configured heartbeat interval are immediately marked as AGENT_UNHEALTHY. This aggressive detection is possible **because heartbeats are lightweight** - they carry no resource data.

### 6.4 Resource Telemetry (Separate Channel)

**MetricsReport Message**:
```protobuf
message MetricsReport {
  Header header = 1;
  float cpu_percent = 2;        // CPU utilization
  uint64 memory_mb = 3;         // Memory usage
  uint64 requests_handled = 4;  // Request count
  map<string, double> custom_metrics = 5;
}
```

**Transmission**: Separate channel, independent frequency (typically 60s intervals).

**Why This Matters**: Large telemetry payloads cannot starve the control path. This separation is PAP's "zombie-prevention superpower."

---

## 7. Provisioning Protocol

### 7.1 Provisioning Sequence

```
1. Station generates invite token (JWT, short-lived)
2. Agent submits ProvisionRequest with token
3. Station validates token and agent identity
4. Station issues:
   - X.509 client certificate
   - Ed25519 signing key reference
   - DNS entry in a.plugged.in
   - Agent configuration (MCP servers, models, policies)
5. Agent acknowledges and begins heartbeat
```

### 7.2 ProvisionRequest Message

```protobuf
message ProvisionRequest {
  string agent_uuid = 1;           // "namespace/research@v1.2"
  Credentials credentials = 2;     // Temporary or bootstrap creds
  AgentConfiguration configuration = 3;
}

message AgentConfiguration {
  repeated string mcp_servers = 1;  // ["filesystem@v2.1", "web-search@v1.5"]
  repeated string models = 2;       // ["gpt-4", "claude-3"]
  MemoryConfiguration memory = 3;
  map<string, string> policies = 4; // {"max_tokens": "100000"}
}
```

### 7.3 ProvisionResponse Message

```protobuf
message ProvisionResponse {
  ErrorCode status = 1;
  string instance_id = 2;          // Unique instance identifier
  repeated string capabilities = 3; // ["a2a-0.3", "mcp-2025-06-18"]
  string message = 4;
}
```

---

## 8. Authorization and Security

### 8.1 PAP-CP Authentication (Normative)

**Transport Security**:
- Mutual TLS REQUIRED
- Certificate validation REQUIRED
- Hostname verification REQUIRED

**Message Security**:
- Ed25519 signature REQUIRED on all messages
- SHA-256 checksum REQUIRED
- Nonce-based replay protection REQUIRED (≥60s cache)

**Nonce Requirements**:
- 32 bytes of cryptographically random data
- MUST be unique per message
- Stations MUST cache nonces for ≥60 seconds
- Messages with duplicate nonces MUST be rejected with `UNAUTHORIZED`

### 8.2 PAP-Hooks Authentication (Normative)

**Transport Security**:
- TLS 1.3 REQUIRED
- Certificate validation REQUIRED

**Token Security**:
- OAuth 2.1 RECOMMENDED
- JWT bearer tokens with claims:
  - `agent_uuid`: Persistent agent identifier
  - `station_id`: Issuing station
  - `scopes`: Authorized operations
  - `capabilities`: Protocol support
- Token lifetime ≤1 hour RECOMMENDED
- Refresh token rotation REQUIRED

### 8.3 Credential Rotation

**Certificate Rotation**:
- Rotation period: 90 days (default)
- Renewal initiated at 30 days before expiry
- Zero-downtime rotation via dual-certificate support

**Key Rotation**:
- Ed25519 key rotation during certificate renewal
- Old keys retained for 7 days (signature verification)
- New keys used for all new signatures

---

## 9. Error Model and Codebook

### 9.1 Unified Error Codes (Normative)

| Code | HTTP | gRPC | PAP-CP | PAP-Hooks | Policy |
|------|------|------|---------|-----------|---------|
| **OK** | 200 | OK | ✓ | ✓ | Success |
| **ACCEPTED** | 202 | OK | ✓ | ✓ | Async processing |
| **BAD_REQUEST** | 400 | INVALID_ARGUMENT | ✓ | ✓ | Invalid message |
| **UNAUTHORIZED** | 401 | UNAUTHENTICATED | ✓ | ✓ | Auth failure |
| **FORBIDDEN** | 403 | PERMISSION_DENIED | ✓ | ✓ | Policy violation |
| **NOT_FOUND** | 404 | NOT_FOUND | ✓ | ✓ | Target missing |
| **TIMEOUT** | 408 | DEADLINE_EXCEEDED | ✓ | ✓ | Retry ≤3 with jitter |
| **CONFLICT** | 409 | ABORTED | ✓ | ✓ | Version mismatch |
| **RATE_LIMITED** | 429 | RESOURCE_EXHAUSTED | ✓ | ✓ | Exponential backoff |
| **AGENT_UNHEALTHY** | 480 | UNAVAILABLE | ✓ | - | Missed heartbeat |
| **AGENT_BUSY** | 481 | UNAVAILABLE | ✓ | ✓ | Load shedding |
| **DEPENDENCY_FAILED** | 482 | UNAVAILABLE | - | ✓ | Circuit breaker |
| **INTERNAL_ERROR** | 500 | INTERNAL | ✓ | ✓ | Log and alert |
| **PROXY_ERROR** | 502 | UNAVAILABLE | - | ✓ | Gateway issue |
| **VERSION_UNSUPPORTED** | 505 | UNIMPLEMENTED | ✓ | ✓ | Upgrade required |

### 9.2 Error Response Policies

**Retry Policy**:
- `TIMEOUT`: Retry ≤3 times with exponential backoff (1s, 2s, 4s)
- `RATE_LIMITED`: Exponential backoff with jitter, respect `Retry-After` header
- `AGENT_BUSY`: Linear backoff, load balance to alternate agents
- `DEPENDENCY_FAILED`: Circuit breaker opens after 5 consecutive failures

**Circuit Breaker**:
- Threshold: 5 consecutive errors
- Open duration: 30 seconds (minimum)
- Half-open: Single test request
- Success → Closed, Failure → Open (exponential backoff)

---

## 10. Ownership Transfer Protocol

### 10.1 Transfer Sequence

```
1. Old Station: TransferInit
   ↓
2. New Station: TransferAccept (new credentials)
   ↓
3. Agent: Dual connection (both Stations)
   ↓
4. State snapshot transfer (encrypted)
   ↓
5. Old Station: Revoke credentials
   ↓
6. Agent: TransferComplete acknowledgment
```

### 10.2 Transfer Messages

**TransferInit**:
```protobuf
message TransferInit {
  string agent_uuid = 1;
  string target_station = 2;        // "station-b.example.com"
  bool preserve_state = 3;          // Transfer agent memory/state
  google.protobuf.Timestamp initiated_at = 4;
}
```

**TransferAccept**:
```protobuf
message TransferAccept {
  string agent_uuid = 1;
  Credentials new_credentials = 2;  // From target station
  string transfer_token = 3;        // Time-bound authorization
}
```

**TransferComplete**:
```protobuf
message TransferComplete {
  string agent_uuid = 1;
  string old_station = 2;           // "plugged.in"
  string new_station = 3;           // "station-b.example.com"
  bool keys_rotated = 4;
  google.protobuf.Timestamp completed_at = 5;
}
```

### 10.3 State Transfer Security

- State snapshots MUST be encrypted (AES-256-GCM)
- Transfer tokens MUST be time-bound (≤5 minutes)
- Credentials MUST be rotated atomically
- Transfer MUST be logged in immutable audit trail
- Old credentials MUST be revoked immediately after transfer

---

## 11. Observability and Tracing

### 11.1 Trace Context Propagation

**OpenTelemetry Integration**:
```protobuf
message Header {
  string trace_id = 7;     // 16-byte hex string
  string span_id = 8;      // 8-byte hex string
}
```

**W3C Trace Context Headers** (HTTP/WebSocket):
```http
Traceparent: 00-{trace-id}-{span-id}-01
Tracestate: pap=station-plugged.in
```

### 11.2 Logging Requirements

**Structured Logging** (JSON format):
```json
{
  "timestamp": "2025-11-04T12:34:56.789Z",
  "level": "INFO",
  "message": "Provision request received",
  "agent_uuid": "namespace/research@v1.2",
  "instance_id": "inst-abc123",
  "trace_id": "trace-xyz",
  "span_id": "span-123"
}
```

### 11.3 Metrics (Prometheus Format)

**Control Plane Metrics**:
```
pap_cp_heartbeat_latency_seconds{agent, mode} - Heartbeat round-trip time
pap_cp_heartbeat_missed_total{agent} - Missed heartbeat counter
pap_cp_provision_requests_total{status} - Provision request counter
pap_cp_terminate_requests_total{type} - Termination counter
pap_cp_signature_validation_failures_total - Signature failure counter
```

**Hooks Metrics**:
```
pap_hooks_requests_total{agent, hook, method, status}
pap_hooks_request_duration_seconds{agent, hook, method}
pap_hooks_rate_limit_hits_total{agent, hook}
pap_hooks_circuit_breaker_state{hook} - Circuit breaker state (0=closed, 1=open, 2=half-open)
```

---

## 12. Protocol Interoperability

### 12.1 MCP Integration

**Mapping**:
- MCP Resources → Agent memory/state (PAP-CP)
- MCP Tools → Tool invocations (PAP-Hooks)
- MCP Prompts → Template library (PAP-Hooks)

**Example**:
```json
// MCP tool.invoke
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "web-search",
    "arguments": {"query": "quantum"}
  }
}

// PAP-Hooks equivalent
{
  "jsonrpc": "2.0",
  "method": "tool.invoke",
  "params": {
    "tool": "web-search",
    "arguments": {"query": "quantum"},
    "context": {"agent_uuid": "..."}
  }
}
```

### 12.2 A2A Integration

**Mapping**:
- A2A Agent Cards → Service Registry entries
- A2A Task Delegation → `a2a.delegate` method (PAP-Hooks)
- A2A Task States → Lifecycle states (PAP-CP)

**Example**:
```json
{
  "jsonrpc": "2.0",
  "method": "a2a.delegate",
  "params": {
    "target_agent": "namespace/worker@v1.0",
    "task": {
      "type": "analyze",
      "data": {"document_id": "doc-123"}
    }
  }
}
```

---

## 13. Compliance Requirements

### 13.1 Mandatory Features (MUST)

- [ ] PAP-CP: gRPC transport with TLS 1.3
- [ ] PAP-CP: Mutual TLS authentication
- [ ] PAP-CP: Ed25519 message signatures
- [ ] PAP-CP: SHA-256 checksums
- [ ] PAP-CP: Nonce-based replay protection (≥60s cache)
- [ ] Heartbeat emission (liveness-only, no resource data)
- [ ] Lifecycle state transitions (NEW → PROVISIONED → ACTIVE → TERMINATED)
- [ ] Error code mapping to local exceptions
- [ ] Signature verification before processing
- [ ] OpenTelemetry trace context propagation

### 13.2 Recommended Features (SHOULD)

- [ ] PAP-Hooks: JSON-RPC over WebSocket
- [ ] PAP-Hooks: OAuth 2.1 authentication
- [ ] Metrics emission (separate from heartbeats)
- [ ] Circuit breaker implementation
- [ ] Exponential backoff with jitter
- [ ] Structured logging with trace IDs
- [ ] Certificate auto-renewal
- [ ] Ownership transfer support

### 13.3 Optional Features (MAY)

- [ ] PAP-Hooks: SSE transport
- [ ] Gateway translation (PAP-CP ↔ PAP-Hooks)
- [ ] Multi-region deployment
- [ ] Custom metric gauges
- [ ] Advanced retry policies

---

## 14. Security Considerations

### 14.1 Threat Model

**Adversaries MAY attempt**:
- (T1) Replay attacks on control messages
- (T2) Telemetry flooding to saturate control channels
- (T3) Agent identity hijacking
- (T4) Induced reasoning loops
- (T5) State exfiltration during transfer

**Mitigations**:
- (T1) → Nonce cache with 60s+ retention, signature verification
- (T2) → Strict heartbeat/metrics separation, rate limiting
- (T3) → mTLS with certificate pinning, DNSSEC
- (T4) → Heartbeat monitoring, Station kill authority
- (T5) → Encrypted state snapshots, audit logging

### 14.2 Security Best Practices

**Certificates**:
- Use Ed25519 for signatures (faster, smaller keys)
- Enable OCSP stapling for revocation checking
- Implement certificate pinning for Station connections

**Nonces**:
- Use cryptographically secure random generator
- Cache size: ≥10,000 nonces (memory-efficient: ~640 KB)
- Eviction: FIFO with 60-second minimum retention

**Tokens (PAP-Hooks)**:
- Lifetime ≤1 hour
- Rotate refresh tokens on use
- Revoke on logout or security event
- Store securely (encrypted at rest)

---

## 15. Implementation Guidelines

### 15.1 SDK Requirements

All language SDKs MUST provide:

**PAP-CP Client**:
- gRPC channel management with connection pooling
- mTLS configuration and certificate loading
- Ed25519 signing and verification
- Nonce generation and tracking
- Automatic heartbeat emission
- Lifecycle state management
- Error mapping to local exceptions

**PAP-Hooks Client**:
- WebSocket and SSE transport support
- OAuth 2.1 token management (acquire, refresh, rotate)
- JSON-RPC 2.0 encoding/decoding
- Retry logic with exponential backoff
- Circuit breaker implementation
- Trace context propagation

### 15.2 Gateway Implementation

Gateways MUST implement:
- Token validation (JWT signature and expiry)
- Scope enforcement
- Rate limiting (per-agent, per-hook)
- Circuit breakers (per-hook)
- Request/response logging with trace IDs
- Metrics emission (Prometheus format)
- Hook configuration management

### 15.3 Station Implementation

Stations MUST implement:
- Agent provisioning with credential issuance
- Lifecycle state tracking
- Heartbeat monitoring with AGENT_UNHEALTHY detection
- Force kill authority (signed messages only)
- Ownership transfer coordination
- Audit logging (immutable, append-only)
- Certificate management and auto-renewal

---

## 16. Deployment Reference

See `docs/deployment-guide.md` for:
- Kubernetes deployment manifests
- Traefik ingress configuration
- DNS delegation setup
- Certificate management (Cert-Manager)
- Observability stack integration

---

## 17. Evaluation Methodology

This section defines performance targets and evaluation criteria for PAP v1.0 implementations, as specified in the academic paper.

### 17.1 Performance Metrics

#### E1: Control Plane Latency
**Target**: Sub-50ms P99 latency for control operations under load

- **Heartbeat round-trip**: P50 <5ms, P99 <20ms
- **Control message processing**: P50 <10ms, P99 <50ms
- **Test conditions**: 1,000 concurrent agents, sustained load
- **Measurement**: End-to-end from agent send to Station receive

#### E2: Liveness Detection
**Target**: <0.1% false positive rate with rapid detection

- **False positive rate**: <0.1% (agents incorrectly marked unhealthy)
- **Detection latency**: Within 1.5× configured heartbeat interval
- **Recovery time from UNHEALTHY**: <10 seconds
- **Test conditions**: Network jitter, partial failures, load spikes

#### E3: Throughput
**Target**: 10,000+ requests/second per gateway with linear scaling

- **Single gateway**: 10,000+ requests/second sustained
- **Horizontal scaling**: Linear to 100,000+ requests/second
- **Circuit breaker activation**: <100ms after error threshold
- **Graceful degradation**: 99.9% availability under chaos testing

#### E4: Ownership Transfer
**Target**: <30 seconds with zero downtime

- **Transfer duration**: <30 seconds including state snapshot
- **Credential rotation**: Atomic with zero service disruption
- **Post-transfer error rate**: <0.01%
- **State consistency**: 100% verification via checksums

### 17.2 Security Validation

#### Authentication Enforcement
- **mTLS coverage**: 100% of PAP-CP connections
- **Signature verification**: All control messages validated
- **Replay attack prevention**: Zero successful replays in 10M attempts
- **Token expiry enforcement**: 100% compliance

#### Audit Completeness
- **Control operation logging**: 100% of lifecycle events
- **Tamper detection**: Immutable append-only logs
- **Compliance reporting**: Real-time audit trail generation

### 17.3 Interoperability Testing

#### MCP Integration
- ✓ Tool invocation via PAP-Hooks
- ✓ Resource access patterns
- ✓ 1000+ available MCP servers tested

#### A2A Integration
- ✓ Agent card discovery
- ✓ Task delegation workflows
- ✓ Linux Foundation reference implementation compatibility

#### Framework Compatibility
- ✓ LangChain/LangGraph orchestration patterns
- ✓ CrewAI multi-agent workflows
- ✓ AutoGPT autonomous operation

### 17.4 Chaos Engineering

**Scenarios**:
- Network partitions and latency injection
- Certificate expiration and rotation
- Gateway failures and recovery
- Agent process crashes
- Database unavailability
- DNS resolution failures

**Success Criteria**:
- No silent failures (all failures logged)
- Graceful degradation to safe state
- Automatic recovery within SLA (99.9% availability)
- Zero data loss for committed operations

---

## 18. Limitations and Current Status

### 18.1 Known Limitations

**Single-Region Deployment**:
- Current implementation targets single-region Station deployment
- Multi-region active-active support planned for v1.1
- Cross-region ownership transfer requires manual coordination

**Synchronous State Transfer**:
- Ownership transfer uses synchronous state snapshot
- Large agent states may exceed 30-second target
- Asynchronous replication with CRDTs planned for v1.1

**Scalability Constraints**:
- Single Station instance supports up to 10,000 concurrent agents
- Horizontal Station scaling requires careful state partitioning
- Global agent namespace coordination needed for federation

**Protocol Versioning**:
- Current version negotiation is binary (support or reject)
- Graceful degradation for partial feature support not yet defined
- Forward/backward compatibility requires careful schema evolution

### 18.2 Implementation Status

**✅ Completed**:
- Protocol specification (PAP v1.0)
- Wire format definition (Protocol Buffers v3)
- Dual-profile architecture (PAP-CP + PAP-Hooks)
- Security model (mTLS, Ed25519, OAuth 2.1)
- Lifecycle state machine
- Error codebook
- DNS addressing scheme
- Deployment reference (Kubernetes/Traefik)

**🔄 In Progress**:
- SDK implementations (TypeScript, Python, Rust, Go)
- Gateway service with protocol translation
- Station service with provisioning and lifecycle management
- Conformance test suite

**📋 Planned**:
- Production hardening and performance tuning
- Formal verification (TLA+)
- Multi-region deployment patterns
- Advanced policy DSL

### 18.3 Open Research Questions

**Agent State Management**:
- Optimal state snapshot formats for large contexts
- Incremental state transfer protocols
- State compression and deduplication strategies

**Federated Identity**:
- DID integration for cross-Station trust
- Verifiable credentials for agent capabilities
- Trust anchors and root of trust establishment

**Performance Optimization**:
- Binary protocol alternatives to Protocol Buffers
- Zero-copy message passing for high-throughput scenarios
- Hardware acceleration for signature verification

---

## 19. Future Extensions

**Planned for v1.1**:
- Multi-region active-active Station deployment
- Asynchronous state replication (CRDTs)
- Federated identity with DIDs
- Advanced policy DSL
- Binary protocol optimizations

**Research Directions**:
- Formal verification of protocol safety (TLA+)
- Zero-trust networking with SPIFFE/SPIRE
- Confidential computing integration
- Quantum-resistant cryptography

---

## 20. References

### Academic Paper
[0] C. Karaca, "The Plugged.in Agent Protocol (PAP): A Comprehensive Framework for Autonomous Agent Lifecycle Management," Draft v0.3 for arXiv cs.DC, VeriTeknik & Plugged.in, November 2025.

### Protocol Specifications
[1] Anthropic, "Model Context Protocol Specification," Available: https://modelcontextprotocol.io/specification/2025-06-18/, 2025.

[2] Linux Foundation, "Agent-to-Agent Protocol (A2A) Specification v0.3," Available: https://a2a-protocol.org/latest/specification/, 2025.

[3] [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification)

[4] [OAuth 2.1 Draft](https://oauth.net/2.1/)

### Standards
- [RFC 9110: HTTP Semantics](https://datatracker.ietf.org/doc/html/rfc9110)
- [RFC 8446: TLS 1.3](https://datatracker.ietf.org/doc/html/rfc8446)
- [RFC 8032: Ed25519 Signatures](https://datatracker.ietf.org/doc/html/rfc8032)
- [RFC 2136: DNS UPDATE](https://datatracker.ietf.org/doc/html/rfc2136)
- [OpenTelemetry Specification](https://opentelemetry.io/docs/specs/otel/)

### Agent Systems Research
[5] V. de Lamo Castrillo, H. K. Gidey, A. Lenz, and A. Knoll, "Fundamentals of Building Autonomous LLM Agents," arXiv:2510.09244, 2025.

[6] H. Tran, et al., "Multi-Agent Collaboration Mechanisms: A Survey of LLMs," arXiv:2501.06322, 2025.

[7] Y. He, et al., "Security of AI Agents," arXiv:2406.08689v2, 2024.

[8] Y. Ding, et al., "Multi-Agent Coordination via Multi-Level Communication," Proceedings of NeurIPS 2024.

### Governance and Security
[9] "MI9 - Agent Intelligence Protocol: Runtime Governance for Agentic AI Systems," arXiv:2508.03858v1, 2025.

[10] "TRiSM for Agentic AI: Trust, Risk, and Security Management in LLM-based Multi-Agent Systems," arXiv:2506.04133v1, 2025.

### Interoperability
[11] "A Survey of Agent Interoperability Protocols: MCP, ACP, A2A, and ANP," arXiv:2505.02279v1, 2025.

---

## Changelog

### v1.0 (November 12, 2025)
- Introduced dual-profile architecture (PAP-CP + PAP-Hooks)
- Strict heartbeat/metrics separation (zombie-prevention superpower)
- Normative lifecycle states (NEW → PROVISIONED → ACTIVE → TERMINATED)
- Ownership transfer protocol
- Comprehensive error codebook with retry policies
- OAuth 2.1 authentication for PAP-Hooks
- Service registry schema
- Protocol interoperability (MCP, A2A)

### rev2.1 (Previous)
- Added trace_id/span_id to envelope
- Clarified heartbeat liveness-only semantics
- Documented DNS delegation

---

**Document Version**: 1.0
**Status**: Stable Candidate
**Last Updated**: November 12, 2025
**Protocol Version**: PAP v1.0
**Paper Version**: Draft v0.3 (for arXiv cs.DC)
**Specification Repository**: https://github.com/VeriTeknik/PAP
