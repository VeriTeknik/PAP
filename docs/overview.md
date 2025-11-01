# Plugged.in Agent Protocol (PAP) Overview

## Mission
PAP delivers a secure, auditable control channel between the Plugged.in Station and every autonomous Satellite. It merges infrastructure operations with agent cognition: lifecycle orchestration, telemetry, routing, and emergency authority live alongside fast bidirectional messaging.

## Vision
- **Autonomy without anarchy**: Satellites operate independently yet respect Station mandates for provisioning, policy, and termination.
- **Infrastructure-grade accountability**: DNS-based identities, mutual TLS, signed payloads, and full telemetry archives.
- **Lifecycle awareness**: Bootstrap, heartbeat, failover, migration, and kill flows are primitives, not afterthoughts.

## Roles
- **Station**: Authentication, routing, policy enforcement, kill authority.
- **Satellite**: Mission execution, telemetry emission, self-healing, graceful exits.
- **Proxy (mcp.plugged.in)**: Terminates TLS, validates signatures, enforces quota, forwards responses and events.

## Addressing & Topology
- Identity: `{agent}.{cluster}.a.plugged.in`
- Platform: Kubernetes (Rancher managed), Traefik ingress with wildcard certificates.
- Telemetry: Routed through the Station for logging, alerting, and replay.

## Message Families
- `invoke`: Station or peer-issued commands.
- `response`: Synchronous or asynchronous acknowledgments.
- `event`: Telemetry, heartbeats, alerts, logs.
- `error`: Structured fault reporting with standardized codes.

## Guardrails
- Continuous heartbeats with CPU/memory metrics prevent zombie processes.
- Kill authority remains exclusive to the Station and requires signed control messages.
- Ownership transfer preserves agent identity across Stations with replay protection.

## Roadmap Snapshot
1. Finalize PAP-RFC-001 (transport, schema, lifecycle).
2. Ship SDKs (TypeScript, Python, Rust, Go) with signing, retries, telemetry.
3. Build PAP Proxy with mTLS, JWT onboarding, OpenTelemetry exports.
4. Implement Registry & Policy service for capabilities and IAM-style controls.
5. Provide deployment assets (Helm charts, manifests) for marketplace integration.
