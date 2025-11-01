# Plugged.in Agent Protocol (PAP)

PAP is the control and telemetry backbone that connects Plugged.in's core control plane (the Station) with autonomous agents (the Satellites). The protocol defines how agents authenticate, exchange commands, stream telemetry, negotiate lifecycle events, and remain accountable to centralized policy without losing their autonomy.

## Architecture Overview

```mermaid
graph TB
    subgraph Station["🛰️ The Station (Plugged.in Core)"]
        Registry["Registry & Identity"]
        Policy["Policy Engine"]
        Memory["Memory Service"]
        Control["Control Center"]
    end

    subgraph Proxy["PAP Proxy (mcp.plugged.in)"]
        Auth["🔐 mTLS Auth"]
        Router["🔀 Message Router"]
        Logger["📊 Telemetry Logger"]
        RateLimit["⏱️ Rate Limiter"]
        Sig["✍️ Signature Verify"]
    end

    subgraph Shuttles["🚀 Autonomous Agents (Shuttles)"]
        Focus["Focus Agent<br/>focus.cluster.a.plugged.in"]
        MemAgent["Memory Agent<br/>memory.cluster.a.plugged.in"]
        Edge["Edge Agent<br/>edge.cluster.a.plugged.in"]
        Custom["Custom Agent<br/>custom.cluster.a.plugged.in"]
    end

    Station <-->|Commands<br/>Telemetry| Proxy
    Proxy <-->|invoke<br/>response<br/>event| Focus
    Proxy <-->|invoke<br/>response<br/>event| MemAgent
    Proxy <-->|invoke<br/>response<br/>event| Edge
    Proxy <-->|invoke<br/>response<br/>event| Custom

    Focus -.->|heartbeat| Proxy
    MemAgent -.->|heartbeat| Proxy
    Edge -.->|heartbeat| Proxy
    Custom -.->|heartbeat| Proxy

    Control -.->|🔴 KILL| Proxy

    style Station fill:#1e3a8a,stroke:#3b82f6,color:#fff
    style Proxy fill:#064e3b,stroke:#10b981,color:#fff
    style Shuttles fill:#581c87,stroke:#a855f7,color:#fff
    style Control fill:#7f1d1d,stroke:#ef4444,color:#fff
```

## Message Flow

```mermaid
sequenceDiagram
    participant Core as 🛰️ Station Core
    participant Proxy as PAP Proxy
    participant Agent as 🚀 Agent (Shuttle)

    Note over Core,Agent: Provisioning Phase
    Core->>Agent: Invite Token (JWT)
    Agent->>Proxy: Authenticate + Register
    Proxy->>Core: Validate Identity
    Core->>Agent: Certificate + DNS ID

    Note over Core,Agent: Operation Phase
    loop Heartbeat (every 30s)
        Agent-->>Proxy: HeartbeatEvent (mode, uptime)
        Proxy-->>Core: Log Telemetry
    end

    Core->>Proxy: invoke Command
    Proxy->>Agent: invoke (signed)
    Agent->>Agent: Execute Task
    Agent->>Proxy: response (result)
    Proxy->>Core: response

    Agent->>Proxy: event (metrics, logs)
    Proxy->>Core: Store in Memory Service

    Note over Core,Agent: Zombie Detection
    Agent--xProxy: ❌ Heartbeat Missed
    Proxy->>Core: 🚨 AGENT_UNHEALTHY
    Core->>Proxy: terminate Command
    Proxy->>Agent: Graceful Shutdown

    Note over Core,Agent: Emergency Kill
    Core->>Proxy: 🔴 force_kill
    Proxy->>Agent: -9 Immediate Termination
```

## Repository Map

- `docs/`: Human-readable specifications and architectural notes.
  - `overview.md`: Narrative overview of the mission, vision, and why PAP exists.
  - `rfc/pap-rfc-001.md`: Draft transport specification (handshake, message schema, lifecycle flows).
- `proto/`: Protocol Buffers definitions and related guidance.
  - `pap/v1/pap.proto`: Initial wire schema for v1 messages.
  - `README.md`: Instructions for working with protobuf tooling.
- `sdk/`: Language-specific SDK plans and future implementations.
  - `README.md`: Current goals, parity guidelines, and open tasks.
- `proxy/`: PAP proxy and network edge notes.
- `registry/`: Identity, policy, and capability management plans.
- `ops/`: Operational runbooks, heartbeat thresholds, and SLO tracking.

## Heartbeat Semantics

- Heartbeat is a liveness-only signal. It must never be used as a readiness gate for accepting work. Readiness should be determined by separate health checks or internal state transitions.
- Default interval: 10s (configurable). Unhealthy threshold: 3 consecutive misses, triggering `AGENT_UNHEALTHY`.
- Resource gauges (CPU, memory, custom) belong in heartbeat; business and performance metrics should be emitted separately as `event.metrics`.

## DNS Topology

- Base zone: `plugged.in`
- Proxy edge: `mcp.plugged.in` (TLS termination, routing, rate limits)
- Agent namespace: `{agent}.{cluster}.a.plugged.in` (delegated `a.plugged.in` subzone)
- Delegation model:
  - `mcp.plugged.in` → Station-owned LB/frontdoor
  - `a.plugged.in` → Cluster-level DNS, aligned with certificate SANs and DNSSEC

## Error Codes (Summary)

| Enum | HTTP | Description |
|------|------|-------------|
| `OK` | 200 | Request completed successfully. |
| `ACCEPTED` | 202 | Task accepted; processing async. |
| `BAD_REQUEST` | 400 | Invalid message or arguments. |
| `UNAUTHORIZED` | 401 | Invalid or missing credentials. |
| `FORBIDDEN` | 403 | Action not permitted. |
| `NOT_FOUND` | 404 | Target agent/action not found. |
| `TIMEOUT` | 408 | Job or agent timeout. |
| `CONFLICT` | 409 | Version or concurrency conflict. |
| `RATE_LIMITED` | 429 | Too many requests. |
| `AGENT_UNHEALTHY` | 480 | Heartbeat anomaly detected. |
| `AGENT_BUSY` | 481 | Agent overloaded; retry later. |
| `DEPENDENCY_FAILED` | 482 | Downstream call failed. |
| `INTERNAL_ERROR` | 500 | Agent internal fault. |
| `PROXY_ERROR` | 502 | Routing/connection issue. |
| `VERSION_UNSUPPORTED` | 505 | Protocol version mismatch. |

## Message Types

PAP defines four canonical message families for all communication:

```mermaid
graph TB
    subgraph MsgTypes["📨 PAP Message Types"]
        Invoke["<b>invoke</b><br/>Command from Station<br/>or peer agent"]
        Response["<b>response</b><br/>Acknowledgment<br/>or result"]
        Event["<b>event</b><br/>Telemetry:<br/>heartbeat, logs, alerts"]
        Error["<b>error</b><br/>Structured failure<br/>with retry policy"]
    end

    Station[Station] -->|Command| Invoke
    Invoke -->|via Proxy| Agent1[Agent]

    Agent1 -->|Result| Response
    Response -->|via Proxy| Station

    Agent1 -->|Heartbeat| Event
    Event -->|via Proxy| Watchdog[Watchdog]

    Agent1 -->|Failure| Error
    Error -->|via Proxy| ErrorHandler[Error Handler]
    ErrorHandler -->|Retry?| Agent1
    ErrorHandler -->|Give up| Station

    Agent1 -.->|Invoke peer| Agent2[Another Agent]
    Agent2 -.->|Response| Agent1

    style Invoke fill:#e3f2fd
    style Response fill:#e8f5e9
    style Event fill:#fff3e0
    style Error fill:#ffebee
```

## Getting Started

1. Read `docs/overview.md` to understand the protocol vision.
2. Dive into `docs/rfc/pap-rfc-001.md` for transport-level requirements, or the rev2.1-aligned spec at `docs/rfc/pap-rfc-001-rev2.1.md`.
3. Generate language stubs from `proto/pap/v1/pap.proto` once SDK work begins.

### Observability & Tracing

- All messages should carry OpenTelemetry identifiers (`trace_id`, `span_id`) in the envelope for end-to-end correlation through the Proxy and Station.
- The Proxy is responsible for emitting traces with these identifiers and linking to upstream/downstream spans.

## Status
This repository targets PAP-RFC-001 rev2.1 alignment. Specifications and schemas may evolve; see `VERSION` and `CHANGELOG.md` for updates.

## Contributing
Please open issues or drafts for changes to specs, schemas, or operational playbooks. Align proposal discussions with the RFC structure documented under `docs/rfc/`.

See `CODE_OF_CONDUCT.md` and `SECURITY.md` for governance and vulnerability reporting.

## License
PAP is released under the Apache 2.0 License. See `LICENSE` for the full text and patent grant.
