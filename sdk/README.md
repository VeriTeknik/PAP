# PAP SDKs

This directory will host language-specific client and server SDKs that implement the PAP transport, authentication, telemetry helpers, and lifecycle primitives.

## Target Languages
1. **TypeScript** — Browser-friendly and Node runtimes; ideal for control plane integrations.
2. **Python** — Data and automation agents.
3. **Rust** — Systems-level agents and proxies.
4. **Go** — Infrastructure services and Station components.

## Shared Requirements

- Wrap signing and verification helpers for PAP envelopes.
- Provide heartbeat emitters with pluggable health probes.
- Offer retry-aware `invoke` helpers with deadline propagation.
- Surface structured errors mapped to PAP `ErrorCode`.
- Ship conformance tests that exercise handshake, invoke, event, and lifecycle flows.

## Key Design: Heartbeat vs Metrics Separation

```mermaid
graph LR
    subgraph Agent["🚀 Agent"]
        HB[Heartbeat<br/>Generator]
        MG[Metrics<br/>Collector]
    end

    subgraph Proxy["PAP Proxy"]
        HBH[Heartbeat<br/>Handler]
        MH[Metrics<br/>Handler]
    end

    subgraph Station["Station"]
        Watchdog[Watchdog<br/>Monitor]
        Metrics[Metrics<br/>Store]
    end

    HB -->|"Every 10s<br/>Liveness Signal"| HBH
    HBH -->|"Liveness Status"| Watchdog

    MG -->|"cpu_percent<br/>memory_mb<br/>disk_io"| MH
    MH -->|"Resource Data"| Metrics

    Watchdog -->|"⚠️ Missed 2 heartbeats"| Agent
    Watchdog -->|"🚨 Force Kill"| Agent

    style HB fill:#ffecb3
    style HBH fill:#ffecb3
    style Watchdog fill:#ffccbc
    style MG fill:#c8e6c9
    style MH fill:#c8e6c9
    style Metrics fill:#c8e6c9
```

**Rationale:** Heartbeats are lightweight liveness signals sent at consistent intervals. Resource metrics (CPU, memory, disk) are collected separately and can be sent at different frequencies or batched. This separation ensures zombie detection remains reliable even under high load.

## Directory Plan
```
sdk/
  typescript/      # Node/browser SDK
  python/          # Python package (pyproject + dataclasses)
  rust/            # Cargo crate
  go/              # Go module
  tests/           # Protocol compliance suites
```

Baseline scaffolding is in place. Each SDK SHOULD now add generated protobuf bindings and runnable examples mirroring the flows described in `docs/rfc/pap-rfc-001.md`.
