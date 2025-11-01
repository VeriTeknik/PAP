# Plugged.in Agent Protocol (PAP)

PAP is the control and telemetry backbone that connects Plugged.in's core control plane (the Station) with autonomous agents (the Satellites). The protocol defines how agents authenticate, exchange commands, stream telemetry, negotiate lifecycle events, and remain accountable to centralized policy without losing their autonomy.

## Architecture Overview

```mermaid
graph TB
    subgraph Station["🛸 Station (Plugged.in Core)"]
        Registry[Registry]
        Policy[Policy Engine]
        Memory[Memory Service]
        Control[Control Center]
    end

    subgraph Proxy["🔐 PAP Proxy (mcp.plugged.in)"]
        Auth[mTLS Auth]
        Router[Message Router]
        Logger[Event Logger]
        RateLimit[Rate Limiter]
    end

    subgraph Agents["🚀 Autonomous Agents"]
        Focus[Focus Agent<br/>focus.us-east.a.plugged.in]
        Analytics[Analytics Agent<br/>analytics.eu.a.plugged.in]
        Memory2[Memory Agent<br/>memory.us-west.a.plugged.in]
        Edge[Edge Agent<br/>edge.asia.a.plugged.in]
    end

    Station -->|Commands<br/>Kill Authority| Proxy
    Proxy <-->|Heartbeat<br/>Metrics<br/>Events| Agents

    Focus -.->|Invoke| Proxy
    Proxy -.->|Route| Analytics

    Station -->|"⚠️ FORCE KILL"| Focus

    classDef stationStyle fill:#e1f5ff,stroke:#0066cc,stroke-width:3px
    classDef proxyStyle fill:#fff4e6,stroke:#ff9800,stroke-width:2px
    classDef agentStyle fill:#e8f5e9,stroke:#4caf50,stroke-width:2px

    class Station stationStyle
    class Proxy proxyStyle
    class Agents agentStyle
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
2. Dive into `docs/rfc/pap-rfc-001.md` for transport-level requirements.
3. Generate language stubs from `proto/pap/v1/pap.proto` once SDK work begins.

## Status
This repository contains the initial scaffolding for PAP v1.0. Specifications are in draft form and subject to change as infrastructure and SDK work progress.

## Contributing
Please open issues or drafts for changes to specs, schemas, or operational playbooks. Align proposal discussions with the RFC structure documented under `docs/rfc/`.

## License
PAP is released under the Apache 2.0 License. See `LICENSE` for the full text and patent grant.
